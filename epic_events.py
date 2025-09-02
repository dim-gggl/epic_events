from crm.cli import build_parser, epic_events_crm
from observability import init_sentry


def main(argv=None):
    init_sentry()
    parser = build_parser()
    epic_events_crm()


if __name__ == "__main__":
    main()