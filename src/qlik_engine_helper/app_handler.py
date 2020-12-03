import json
import logging
from enum import Enum, unique
from typing import Any, Dict, List, Tuple, Union

import websockets

from qlik_engine_helper.api_methods import ApiMethods


class AppHandler:
    @unique
    class ConnectionState(Enum):
        DISCONNECTED = 0
        CONNECTED = 1

    @unique
    class AppState(Enum):
        VOID = 0
        CREATE = 1
        OPEN = 2
        CLOSED = 3

    _state_connection: ConnectionState = ConnectionState.DISCONNECTED
    _state_app: AppState = AppState.VOID

    def __init__(self, ws_url: str) -> None:
        self.ws_url = ws_url

        self._conn = None
        self._handle = None

    # States
    @property
    def connection_state(self) -> ConnectionState:
        return self._state_connection

    @connection_state.setter
    def connection_state(self, new_state: ConnectionState) -> None:
        assert isinstance(new_state, self.ConnectionState)
        self._state_connection = new_state

    @property
    def app_state(self) -> AppState:
        return self._state_app

    @app_state.setter
    def app_state(self, new_state: AppState) -> None:
        assert isinstance(new_state, self.AppState)
        self._state = new_state

    # Connect / Disconnect
    async def connect(self) -> None:
        self._conn = await websockets.connect(self.ws_url)

        response = json.loads(await self._conn.recv())
        session_state = response["params"]["qSessionState"]

        if session_state == "SESSION_CREATED":
            print("Connected!")
            self.state = self.ConnectionState.CONNECTED
        else:
            raise Exception(f"Connection could not be created! \n\t Trace: {response}")

    async def disconnect(self) -> None:
        await self._conn.close()

        self._conn = None
        self._handle = None
        self.connection_state = self.ConnectionState.DISCONNECTED
        self.state = self.AppState.CLOSED

        print("Disconnected!")

    @property
    def handle(self) -> int:
        return self._handle  # type: ignore

    @handle.setter
    def handle(self, handle: int):
        if self.state == self.AppState.OPEN:
            self._handle = handle

    @staticmethod
    def create_request(method: str, app_handle: int, params: List[str]) -> str:
        """Creates JSON RPC request for the Qlik API

        Args:
            method (str): The API method to be called
            app_handle (int): The handle of the app, -1 on global level
            params (list[str]): Parameters for the selected method

        Returns:
            str: JSON formatted payload string
        """
        payload = dict(jsonrpc="2.0", method=method, handle=app_handle, params=params)

        return json.dumps(payload)

    async def send_request(self, request: str) -> Dict[str, Any]:
        await self._conn.send(request)
        response = await self._conn.recv()
        return json.loads(response)

    # API Interaction
    async def create_app(self, app_name: str) -> Union[str, None]:

        if not app_name.endswith(".qvf"):
            app_name += ".qvf"

        request = self.create_request(
            method=ApiMethods.create_app.value,
            app_handle=-1,
            params=[f"{app_name.strip()}"],
        )

        response = await self.send_request(request)
        logging.debug(response)

        try:

            success = response["result"]["qSuccess"]
            if not success:
                print("App create command was processed but not successful")
                return None

            app_id = response["result"]["qAppId"]  # Path to qvf or server app id

            self.state = self.AppState.CREATE
            print("Created App")

            return app_id

        except KeyError:
            raise Exception(f"App could not be created. \n\tTrace: {response}")

    async def open_app(self, app_id: str) -> Tuple[str, str]:

        request = self.create_request(
            method=ApiMethods.open_app.value,
            app_handle=-1,
            params=[f"{app_id}"],
        )

        response = await self.send_request(request)

        try:
            print("Opened App")
            logging.debug(response)

            return_values = response["result"]["qReturn"]
            self.state = self.AppState.OPEN
            self.handle = return_values["qHandle"]

            return return_values["qType"], return_values["qHandle"]
        except KeyError:
            raise Exception(f"App could not be opened. \n\tTrace: {response}")

    async def get_script_code(self) -> str:

        if self.state != self.AppState.OPEN:
            raise Exception("App has to be open to get app script code")

        request = self.create_request(
            method=ApiMethods.get_script.value,
            app_handle=self.handle,
            params=[],
        )

        response = await self.send_request(request)

        try:
            script_code = response["result"]["qScript"]
            return script_code
        except KeyError:
            raise Exception(f"Could not retrieve app script code. \n\t{response}")

    async def set_script_code(self, script_code: str) -> None:

        if self.state != self.AppState.OPEN:
            raise Exception("App has to be open to set app script code")

        request = self.create_request(
            method=ApiMethods.set_script.value,
            app_handle=self.handle,
            params=[script_code],
        )

        response = await self.send_request(request)

        try:
            new_code = response["result"]
            print("New script code set")
            return new_code
        except KeyError:
            raise Exception(f"New script code could could not be set. \n\t{response}")

    async def save_app(self) -> bool:

        if self.state != self.AppState.OPEN:
            raise Exception("App has to be open to set app script code")

        request = self.create_request(
            method=ApiMethods.save_app_changes.value,
            app_handle=self.handle,
            params=[],
        )

        response = await self.send_request(request)

        if "result" in response.keys():
            print("App changes saved")
            return True

        print("App changes could not be saved")
        return False

    async def get_app_list(self) -> List[dict]:

        if self.state != self.ConnectionState.CONNECTED:
            raise Exception("Connection needs to be established first!")

        request = self.create_request(
            method=ApiMethods.get_app_list.value,
            app_handle=-1,
            params=[],
        )

        response = await self.send_request(request)

        try:
            app_list: List[dict] = response["result"]["qDocList"]
            return app_list

        except KeyError:
            raise Exception("Could not retrieve App List")
