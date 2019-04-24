"""Add the environment paths to the args input"""

from os.path import join


def setup_path(args):
    """Set paths to the args"""

    setattr(args, "SOURCE", args.dataset_dir)
    setattr(args, "SOURCE_BACKUP", f"{args.SOURCE}_backup")
    setattr(args, "OUTPUT", join(args.output_dir, args.SOURCE))

    setattr(args, "LOG", join(args.OUTPUT, "log"))
    setattr(args, "DATA", join(args.SOURCE, "lines"))
    setattr(args, "GROUND_TRUTH", join(args.SOURCE, "ground_truth"))
    setattr(args, "PREPROC", join(args.SOURCE, "lines_preproc"))
    setattr(args, "PARTITIONS", join(args.SOURCE, "partitions"))

    setattr(args, "TRAIN_FILE", join(args.PARTITIONS, "train.txt"))
    setattr(args, "VALIDATION_FILE", join(args.PARTITIONS, "validation.txt"))
    setattr(args, "TEST_FILE", join(args.PARTITIONS, "test.txt"))

    return args