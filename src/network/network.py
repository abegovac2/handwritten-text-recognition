from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, PReLU, BatchNormalization
from tensorflow.keras.layers import TimeDistributed, Activation, Dense, Bidirectional, LSTM
from tensorflow.keras.callbacks import TensorBoard, EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adamax
from network.ctc_model import CTCModel
import tensorflow.keras.backend as K
import os


class HTRNetwork:

    def __init__(self, output, dtgen):
        self.checkpoint = os.path.join(output, "checkpoint_weights.hdf5")
        self.logger = os.path.join(output, "logger.log")

        self.build_network(dtgen.nb_features, dtgen.dictionary, dtgen.training)
        self.build_callbacks(dtgen.training)

        if os.path.isfile(self.checkpoint):
            self.model.load_checkpoint(self.checkpoint)

    def build_network(self, nb_features, nb_labels, training):
        """Build the HTR network: CNN -> RNN -> CTC"""

        # build CNN
        input_data = Input(name="input", shape=(None, nb_features))
        filters = [64, 128, 256, 512]
        pool_sizes, strides = pool_strides(nb_features, len(filters))

        cnn = K.expand_dims(x=input_data, axis=3)

        for i in range(4):
            cnn = Conv2D(filters=filters[i], kernel_size=5, padding="same", kernel_initializer="he_normal")(cnn)
            cnn = PReLU(shared_axes=[1, 2])(cnn)
            cnn = BatchNormalization(trainable=training)(cnn)

            cnn = Conv2D(filters=filters[i], kernel_size=3, padding="same", kernel_initializer="he_normal")(cnn)
            cnn = MaxPooling2D(pool_size=pool_sizes[i], strides=strides[i], padding="valid")(cnn)
            cnn = PReLU(shared_axes=[1, 1])(cnn)
            cnn = BatchNormalization(trainable=training)(cnn)

        outcnn = K.squeeze(x=cnn, axis=2)

        # build CNN
        blstm = Bidirectional(LSTM(units=512, return_sequences=True, kernel_initializer="he_normal"))(outcnn)
        dense = TimeDistributed(Dense(units=len(nb_labels) + 1, kernel_initializer="he_normal"))(blstm)
        outrnn = Activation(activation="softmax")(dense)

        # create and compile CTC model
        self.model = CTCModel(
            inputs=[input_data],
            outputs=[outrnn],
            greedy=False,
            beam_width=100,
            top_paths=1,
            charset=nb_labels)

        self.model.compile(optimizer=Adamax(learning_rate=0.0001))

    def build_callbacks(self, training):
        """Build/Call callbacks to the model"""

        tensorboard = TensorBoard(
            log_dir=os.path.dirname(self.checkpoint),
            histogram_freq=1,
            profile_batch=0,
            write_graph=True,
            write_images=True,
            update_freq="epoch")

        earlystopping = EarlyStopping(
            monitor="val_loss",
            min_delta=1e-5,
            patience=5,
            restore_best_weights=True,
            verbose=1)

        checkpoint = ModelCheckpoint(
            filepath=self.checkpoint,
            period=1,
            monitor="val_loss",
            save_best_only=True,
            save_weights_only=True,
            verbose=1)

        self.callbacks = [tensorboard, earlystopping, checkpoint]


def pool_strides(nb_features, nb_layers):
    factores, pool, strides = [], [], []

    for i in range(2, nb_features + 1):
        while nb_features % i == 0:
            nb_features = nb_features / i
            factores.append(i)

    order = sorted(factores, reverse=True)
    cand = order[:nb_layers]
    order = order[nb_layers:]

    for i in range(len(cand)):
        if len(order) == 0:
            break
        cand[i] *= order.pop()

    for i in range(nb_layers):
        pool.append((int(cand[i] / 2), cand[i]))
        strides.append((1, cand[i]))

    return pool, strides