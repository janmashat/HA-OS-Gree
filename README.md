# Home Assistant: Gree Climate custom integration with Horizontal Swing support
HA Gree climate as custom integration that work from another LAN segment, you can specify AC IP address.
Done because HA team decided not to update the official Gree integration to work from any LAN segment.<br>
<br>
If you are an advanced user, have a look at Fake-Gree-server: https://github.com/rapi3/Fake-Gree-server<br>
<br>
Please add your HA version if it work for you at Discussion section if you want to help others.<br><br>
For me it work on this version from 2025 because I'm not brave enough to update my running HA and start fixing new problems:<br>
| Name | Version |
| -------- | ------- |
| Core | 2025.4.2 |
| Supervisor | 2025.04.0 |
| Operating System | 15.1 |
| Frontend | 20250411.0 |

# HACS installation:<br>
search on HACS integration for Gree climate integration that work from another LAN segment / you can specify AC IP address or add manual the repository:<br>

1. Go to Home Assistant and navigate to HACS.
2. In HACS, select "Integrations".
3. Click on the three dots button in the upper right corner and select "Custom repositories".
4. In the window that appears, enter the URL of this repository https://github.com/janmashat/HA-OS-Gree and select the category (Integration).
5. Click on "Add".

# Manual instalation:
1. copy all from gree to custom_components/gree/<br>
2. restart HA<br>
3. check log for errors<br>

Set-up:<br>
If no errors then go to Integration - Add integration - Gree Climate and enter AC IP if it is not found automaticaly.<br>
   
If AC it is find and set-up OK check your Gree Climate - Integration entries and rename switches if required, you can find the switch name in core.entity_registry:<br>
     "entity_id": "switch.MAC_none"    ->  Panel Light<br>
     "entity_id": "switch.MAC_none_2"  ->  Quiet<br>
     "entity_id": "switch.MAC_none_3"  ->  Fresh Air<br>
     "entity_id": "switch.MAC_none_4"  ->  XFan<br>
     "entity_id": "switch.MAC_none_5"  ->  Health mode<br>

DONE<br>
<br>
This integration is based on rapi3's fork of the original HA OS Gree Climate (patch from kspearrin)
