#SNP  - SkyNet Protocol description

## 1. Packet descriptions
### 1.1 UDP packet
* Type (1 octet)
 * 1 - Search SD
 * 2 - Answer SD
 * 3 - Field change
* IP SM (4 octets)
* IP SD (4 octets)
* Device id(1 octet)
* Field

### 1.2 TCP packet
* Type (1 octet)
 * 4 - Open key exchange
 * 5 - Register SD
 * 6 - Get device data
 * 7 - Update device state
* IP SM (4 octets)
* IP SD (4 octets)
* Payload
  * Open key exchange
    * Request or answer
    * Key Size (4 octets)
    * Key
  * Registration
    * PIN (4 octets)
    * Devices number (1 octet)
    * Devices
      * ID (1 octet)
      * Device name (128 octets)
      * Field number (1 octet)
      * Fileds
  * Get device data
    * Request or answer (1 octet)
    * ID (1 octet)
    * Device
  * Set device field
    * Request or answer (1 octet)
    * Device ID (1 octet)
    * Field
 
