import uuid
from copy import deepcopy
from enum import Enum
from typing import Dict


def generate_open_parent_folder_action(image_uuid: str = "", title: str = "") -> Dict:
    """Generate an action to open the parent folder."""
    return {
        "ActionID": str(uuid.uuid4()),
        "LinkedTitle": True,
        "Name": "Parent Folder",
        "Plugin": {
            "Name": "Open Parent Folder",
            "UUID": "com.elgato.streamdeck.profile.backtoparent",
            "Version": "1.0",
        },
        "Settings": {},
        "State": 0,
        "States": [
            (
                {
                    "FontFamily": "",
                    "FontSize": 9,
                    "FontStyle": "",
                    "FontUnderline": False,
                    "Image": f"Images/{image_uuid}.png",
                    "OutlineThickness": 2,
                    "ShowTitle": True,
                    "Title": title.replace("-", "\n"),
                    "TitleAlignment": "middle",
                    "TitleColor": "#ffffff",
                }
                if image_uuid
                else {}
            )
        ],
        "UUID": "com.elgato.streamdeck.profile.backtoparent",
    }


class FolderType(Enum):
    MAIN = "main"
    TAXA = "taxa"


def generate_folder_action(
    folder_uuid: str, type: FolderType, image_uuid: str, title: str
) -> Dict:
    """Generate an action to open a subfolder."""
    return {
        "ActionID": str(uuid.uuid4()),
        "LinkedTitle": True,
        "Name": "Create Folder",
        "Plugin": {
            "Name": "Create Folder",
            "UUID": "com.elgato.streamdeck.profile.openchild",
            "Version": "1.0",
        },
        "Settings": {"ProfileUUID": folder_uuid},
        "State": 0,
        "States": [
            {
                "FontFamily": "",
                "FontSize": 9,
                "FontStyle": "",
                "FontUnderline": False,
                "Image": f"Images/{image_uuid}.png",
                "OutlineThickness": 2,
                "ShowTitle": True,
                "Title": (
                    "      [" + title[0:3] + "]"
                    if type == FolderType.TAXA
                    else title.replace("-", "\n")
                ),
                "TitleAlignment": "top" if type == FolderType.TAXA else "middle",
                "TitleColor": "#ffffff",
            }
        ],
        "UUID": "com.elgato.streamdeck.profile.openchild",
    }


def generate_bird_action(
    bird_name: str, image_uuid: str, lightoom: str, uncertain: bool = False
) -> Dict:
    """Generate an action to show bird details."""
    action = {
        "ActionID": str(uuid.uuid4()),
        "Actions": [
            {
                "Actions": [
                    {
                        "ActionID": str(uuid.uuid4()),
                        "LinkedTitle": True,
                        "Name": "Hotkey",
                        "Plugin": {
                            "Name": "Activate a Key Command",
                            "UUID": "com.elgato.streamdeck.system.hotkey",
                            "Version": "1.0",
                        },
                        "Settings": {
                            "Coalesce": True,
                            "Hotkeys": [
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": True,
                                    "KeyModifiers": 2,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 75,
                                    "QTKeyCode": 75,
                                    "VKeyCode": 75,
                                },
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": False,
                                    "KeyModifiers": 0,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 146,
                                    "QTKeyCode": 33554431,
                                    "VKeyCode": -1,
                                },
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": False,
                                    "KeyModifiers": 0,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 146,
                                    "QTKeyCode": 33554431,
                                    "VKeyCode": -1,
                                },
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": False,
                                    "KeyModifiers": 0,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 146,
                                    "QTKeyCode": 33554431,
                                    "VKeyCode": -1,
                                },
                            ],
                        },
                        "State": 0,
                        "States": [{"Title": "Ctrl+K"}],
                        "UUID": "com.elgato.streamdeck.system.hotkey",
                    },
                    {
                        "ActionID": str(uuid.uuid4()),
                        "LinkedTitle": True,
                        "Name": "Text",
                        "Plugin": {
                            "Name": "Text",
                            "UUID": "com.elgato.streamdeck.system.text",
                            "Version": "1.0",
                        },
                        "Settings": {
                            "Hotkey": {
                                "KeyModifiers": 0,
                                "QTKeyCode": 33554431,
                                "VKeyCode": -1,
                            },
                            "isSendingEnter": False,
                            "isTypingMode": False,
                            "pastedText": bird_name,
                        },
                        "State": 0,
                        "States": [{}],
                        "UUID": "com.elgato.streamdeck.system.text",
                    },
                    {
                        "ActionID": "b3c73512-63d7-4878-ba2b-e15f857e7c54",
                        "LinkedTitle": True,
                        "Name": "Delay",
                        "Plugin": {
                            "Name": "Multi Action",
                            "UUID": "com.elgato.streamdeck.multiactions",
                            "Version": "1.0",
                        },
                        "Settings": {"delay": 300},
                        "State": 0,
                        "States": [{}],
                        "UUID": "com.elgato.streamdeck.multiactions.delay",
                    },
                    {
                        "ActionID": "29d9da39-b749-4f19-9f97-b126432e6612",
                        "LinkedTitle": True,
                        "Name": "Hotkey",
                        "Plugin": {
                            "Name": "Activate a Key Command",
                            "UUID": "com.elgato.streamdeck.system.hotkey",
                            "Version": "1.0",
                        },
                        "Settings": {
                            "Coalesce": True,
                            "Hotkeys": [
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": False,
                                    "KeyModifiers": 0,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 27,
                                    "QTKeyCode": 16777216,
                                    "VKeyCode": 27,
                                },
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": False,
                                    "KeyModifiers": 0,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 146,
                                    "QTKeyCode": 33554431,
                                    "VKeyCode": -1,
                                },
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": False,
                                    "KeyModifiers": 0,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 146,
                                    "QTKeyCode": 33554431,
                                    "VKeyCode": -1,
                                },
                                {
                                    "KeyCmd": False,
                                    "KeyCtrl": False,
                                    "KeyModifiers": 0,
                                    "KeyOption": False,
                                    "KeyShift": False,
                                    "NativeCode": 146,
                                    "QTKeyCode": 33554431,
                                    "VKeyCode": -1,
                                },
                            ],
                        },
                        "State": 0,
                        "States": [{"Title": "Esc"}],
                        "UUID": "com.elgato.streamdeck.system.hotkey",
                    },
                ]
            },
            {"Actions": []},
        ],
        "LinkedTitle": True,
        "Name": "Multi Action",
        "Plugin": {
            "Name": "Multi Action",
            "UUID": "com.elgato.streamdeck.multiactions",
            "Version": "1.0",
        },
        "Settings": {},
        "State": 0,
        "States": [
            {
                "FontFamily": "",
                "FontSize": 9,
                "FontStyle": "",
                "FontUnderline": False,
                "OutlineThickness": 2,
                "ShowTitle": True,
                "Title": (
                    "        " + bird_name[0:3]
                    if uncertain == False
                    else bird_name.replace(" (?)", "")[0:6]
                    + (("...") if len(bird_name.replace(" (?)", "")) > 6 else "")
                ),
                "TitleAlignment": "top" if uncertain == False else "bottom",
                "TitleColor": "#ffffff",
                "Image": f"Images/{image_uuid}.png",
            }
        ],
        "UUID": "com.elgato.streamdeck.multiactions.routine",
    }
    steps = action['Actions'][0]['Actions']
    focus_wait = deepcopy(steps[2])
    focus_wait['ActionID'] = str(uuid.uuid4())
    focus_wait['Settings']['delay'] = 500
    submit = deepcopy(steps[3])
    submit['ActionID'] = str(uuid.uuid4())
    submit['States'] = [{'Title': 'Enter'}]
    submit['Settings']['Hotkeys'][0].update(NativeCode=13, QTKeyCode=16777220, VKeyCode=13)
    accept = deepcopy(submit)
    accept['ActionID'] = str(uuid.uuid4())
    accept['States'] = [{'Title': 'Tab'}]
    accept['Settings']['Hotkeys'][0].update(NativeCode=9, QTKeyCode=16777217, VKeyCode=9)
    accept_wait = deepcopy(steps[2])
    accept_wait['ActionID'] = str(uuid.uuid4())
    commit_wait = deepcopy(steps[2])
    commit_wait['ActionID'] = str(uuid.uuid4())
    action['Actions'][0]['Actions'] = [steps[0], focus_wait, steps[1], steps[2], accept, accept_wait, submit, commit_wait, steps[3]]
    return action
