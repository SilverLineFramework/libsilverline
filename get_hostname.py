"""Generate flags used to start the runtime."""

from silverline import parse, parse_args


args = parse_args(parse.mqtt)
print("{}{}:{}".format(
    "ssl://" if args.ssl else "", args.mqtt, args.mqtt_port))
