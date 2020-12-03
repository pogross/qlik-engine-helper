import argparse
import asyncio
import re
from pathlib import Path

from dateutil.parser import parse
from tabulate import tabulate

from qlik_engine_helper.app_handler import AppHandler


def check_app_arg(app_id: str):
    _app_id = str(app_id)
    if not _app_id.endswith("qvf"):
        raise argparse.ArgumentTypeError(
            f"'{app_id}' is not a valid app id. It should end with .qvf",
        )

    return _app_id


def check_url_arg(url: str):
    _url = str(url)
    if not url.startswith("ws://"):
        raise argparse.ArgumentTypeError(
            f"'{_url}' is not a valid websocket url. It should start with ws://",
        )
    return _url


def check_code_path(code_path):
    _code_path = Path(code_path)

    # Can be path
    if _code_path.is_dir():
        if not any(file_path.suffix == ".qvs" for file_path in _code_path.iterdir()):
            raise argparse.ArgumentTypeError(
                f"'{_code_path}' does not contain any .qvs files",
            )

        return _code_path

    # Can be a file
    if _code_path.is_file() and _code_path.suffix != ".qvs":
        raise argparse.ArgumentTypeError(f"'{_code_path}' is not a .qvs file")

    return _code_path


def check_out_path(out_path):
    _out_path = Path(out_path)

    if not _out_path.exists() or not _out_path.is_dir():
        raise argparse.ArgumentTypeError(
            "f{_out_path} is not a valid path or directory",
        )

    return _out_path


def format_tab(name: str) -> str:
    return f"\r\n\r\n///$tab {name}\r\n"


def process_user_code(code_path: Path):

    full_code = ""

    if code_path.is_dir():
        files = [file_path for file_path in code_path.iterdir() if file_path.is_file()]
        combined_files = [
            format_tab(file_path.stem) + file_path.read_text() for file_path in files
        ]
        full_code = "".join(combined_files)

    else:
        tab = format_tab(code_path.stem)
        user_code = code_path.read_text()
        full_code = tab + user_code

    return full_code


async def run():  # noqa C901

    # CLI
    parser = argparse.ArgumentParser(
        description="Qlik Engine Helper",
        prog="qlik-engine-helper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--url",
        default="ws://localhost:4848/app/",
        type=check_url_arg,
        required=False,
        help="The websocket url to your desktop client",
    )

    parser.add_argument(
        "--certs",
        type=str,
        required=False,
        help="Path to server certificates.",
    )

    parser.add_argument(
        "--credentials",
        type=str,
        required=False,
        help="Credentials for server connection.",
    )

    subparsers = parser.add_subparsers(title="commands", dest="command_group")

    # Main Groups
    global_group = subparsers.add_parser("global", help="Set of global commands")
    app_group = subparsers.add_parser("app", help="Set of app commands")

    # Global Commands
    global_commands = global_group.add_subparsers(title="commands", dest="command_name")

    global_cmd = global_commands.add_parser("global-foo", help="a global foo")
    global_cmd.add_argument("--foo", help="Foo argument")

    # App commands
    app_commands = app_group.add_subparsers(title="commands", dest="command_name")

    # List Apps
    app_cmd_create = app_commands.add_parser("list", help="Lists all available apps")

    # Create App
    app_cmd_create = app_commands.add_parser("create", help="Create a new app")
    app_cmd_create.add_argument(
        "--name",
        type=check_app_arg,
        required=True,
        help="The name of the app",
    )

    # Get-Script
    app_cmd_get_script = app_commands.add_parser(
        "get-script",
        help="Gets script code from app",
    )
    app_cmd_get_script.add_argument(
        "--app-id",
        type=check_app_arg,
        required=True,
        help="The App ID (.qvf path for desktop and unique id for server)",
    )

    app_cmd_get_script.add_argument(
        "--out",
        type=str,
        required=False,
        help="Output path where .qvs files should be written to (Path has to exists)",
    )

    # Set-Script
    app_cmd_set_script = app_commands.add_parser(
        "set-script",
        help="Replaces the current app script code",
    )
    app_cmd_set_script.add_argument(
        "--app-id",
        type=check_app_arg,
        required=True,
        help="The App ID (.qvf path for desktop and unique id for server)",
    )
    app_cmd_set_script.add_argument(
        "--code",
        type=check_code_path,
        required=True,
        help="Path to a single qvs file or a folder with qvs files. If a folder is chosen all .qvs files are used",
    )

    # Append-Script
    app_cmd_append_script = app_commands.add_parser(
        "append-script",
        help="Appends script code to the apps current code",
    )
    app_cmd_append_script.add_argument(
        "--app-id",
        type=check_app_arg,
        required=True,
        help="The App ID (.qvf path for desktop and unique id for server)",
    )
    app_cmd_append_script.add_argument(
        "--code",
        type=check_code_path,
        required=True,
        help="Path to a single qvs file or a folder with qvs files. If a folder is chosen all .qvs files are used",
    )

    args = parser.parse_args()

    if not args.command_group:
        print("No valid command selected. Try qlik-engine-helper --help")
        return

    if args.command_group == "global":
        print("Global is not implemented yet :) Bye")
        return

    # App Operations
    app_handler = AppHandler(args.url)

    try:
        await app_handler.connect()

        if args.command_group == "app" and args.command_name == "create":
            await app_handler.create_app(args.name)

        elif args.command_group == "app" and args.command_name == "get-script":
            await app_handler.open_app(args.app_id)
            code = await app_handler.get_script_code()

            tabs = re.findall(r"[\/]{3}\$tab\s*([\d\w ]+)", code)
            split = re.split(r"[\/]{3}\$tab\s*[\d\w ]+", code)

            out_path = args.out if args.out else None  # "."

            if out_path:
                report = []
                for index, (name, content) in enumerate(zip(tabs, split[1:]), 1):
                    file_name = f"{index:03}_{name.strip()}.qvs"
                    file_path = Path(out_path) / file_name
                    report.append([name, file_path.absolute()])

                    with open(file_path, "w") as f:
                        f.write(content.lstrip())

                headers = ["Tab Name", "File Path"]

                print("get-script Results")
                print(tabulate(report, headers, tablefmt="fancy_grid"))
            else:
                print("---- Code Start ----")
                print(code)
                print("---- Code End ----")

        elif args.command_group == "app" and args.command_name == "set-script":

            code = process_user_code(args.code)

            await app_handler.open_app(args.app_id)
            await app_handler.set_script_code(code)
            await app_handler.save_app()

        elif args.command_group == "app" and args.command_name == "append-script":

            # TODO: distinguish path and single file -> iterate procedure
            await app_handler.open_app(args.app_id)

            old_code = await app_handler.get_script_code()
            user_code = process_user_code(args.code)
            full_code = old_code + user_code

            await app_handler.set_script_code(full_code)
            print("Code appended")

            await app_handler.save_app()

        elif args.command_group == "app" and args.command_name == "list":

            app_list = await app_handler.get_app_list()

            headers = ["No.", "Name", "ID", "Last Reload"]
            table = [
                [
                    number,
                    app["qDocName"],
                    app["qDocId"],
                    parse(app["qLastReloadTime"])
                    if "qLastReloadTime" in app.keys()
                    else None,
                ]
                for number, app in enumerate(app_list, start=1)
            ]

            print(tabulate(table, headers, tablefmt="fancy_grid"))

    finally:
        await app_handler.disconnect()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()
