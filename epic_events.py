from crm.cli import build_parser, epic_events_crm


def main(argv=None):

    parser = build_parser()
    epic_events_crm()


if __name__ == "__main__":
    main()