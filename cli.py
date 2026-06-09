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
    similar_parser.add_argument("-k", "--top-k", type=int, default=5, help="Max suggestions to return (tiered: guaranteed >0.80 FAISS first, then hybrid-ranked middle zone)")

    args = parser.parse_args()

    if args.command == "index":
        first_run()

    elif args.command == "update":
        maintenance()

    elif args.command == "similar":
        similar_notes(args.note_name, k=args.top_k)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()