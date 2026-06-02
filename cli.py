import argparse

from agent import first_run, maintenance, similar_notes


def main():
    parser = argparse.ArgumentParser(prog="obs-agent")

    subparsers = parser.add_subparsers(dest="command")

    # index
    subparsers.add_parser("index")

    # update
    subparsers.add_parser("update")

    # similar
    similar_parser = subparsers.add_parser("similar")
    similar_parser.add_argument("note_name")

    args = parser.parse_args()

    if args.command == "index":
        first_run()

    elif args.command == "update":
        maintenance()

    elif args.command == "similar":
        similar_notes(args.note_name)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()