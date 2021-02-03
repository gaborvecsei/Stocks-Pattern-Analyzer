import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--ticker", required=True, help="Anchor ticker (e.g.: GME)")
    parser.add_argument("-w", "--window-size", required=True, help="Pattern size")
    parser.add_argument("-s", "--stocks", default=None, help="Stocks where you'd like to search")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_args()

    data_holder = prepare_data(args.window_size)
    tree = create_search_tree()
    
    
