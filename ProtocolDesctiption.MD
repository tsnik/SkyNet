#SNP  - SkyNet Protocol description

## 1. Abbreviations
* SM - Main server
* SD - Device server
* SC - Control server

## 2. Structure descriptions
### 2.1 Device  
```
{  
	ID : int,  
	Name : string,  
	Fields : [Field]  
}
```

### 2.2 Field
```
{
	Name : string,
	Type : int,
	Writable : bool,
	Value : as Type
}
```
### 2.3 Field types:

1. Bool
2. Int
3. String

## 3. Packet descriptions
### 3.1 Packet types
1. SSD - Search SD
2. ASD - Announce SD
3. FCH - Field change
4. KEX - Open key exchange
5. RSD - Register SD
6. GDF - Get device fields
7. UDF - Update device fields

### 3.2 UDP packet

1 Search SD
```
{
	Type : "SSD",
	Name : string
}
```
2 Anounce SD  
```
{
	Type : "ASD",
	Name : string
}
```
3 Field change  
```
{
	Type : "FCH",
	SDIP : string,
	DevId : int,
	Field : Field
}
```

### 3.3 TCP packet

4 Open key exchange
```
{
	Type : "KEX",
	KEY : string
}
```

5 Register SD
  * Request
```
	{
		Type : "RSD", 
		PIN : int
	}
```
  * Response
```
	{
		Type : "RSD",
		Devices : [Device]
	}
```

6 Get device data
  * Request
```
	{
		Type : "GDF",
		DevId : int
	}
```
  * Response
```
	{
		Type : "GDF",
		Device : Device
	}
```
  
7 Update device data
  * Request
```
	{
		Type : "UDF",
		DevId : int,
		Field : string,
		Value : like field type
	}
```
  * Response
```
	{
		Type : "UDF",
		DevId : int,
		Field : Field
	}
```
	
#SNCP - SkyNet Control Protocol
## 1. Structure descriptions
### 1.1 Method
* Name(128 octets)
* Field number(1 octet)
* Fields
 
### 1.2 Script
* Name(128 octets)
* ID(4 octets)
* Triger
* Action

### 1.3 Triger
* Device ID (4 octets)
* Field name (128 octets)
* Change type(1 octet)
  * 0 - Change
  * 1 - More than
  * 2 - Less than
  * 3 - Equal
* Value (Depends on type)
 
### 1.4 Action
* Type (1 octet)
  * 0 - Field update
  * 1 - Method
* Field update
  * Updating Device ID (4 octets)
  * Updating Field name (128 octets)
  * By field(1) or by value(0) (1 octet)
  * Value (Depends on type)
  * Fetching Device ID
  * Fetching Field name(types should be equal)
* Method
  * Method ID
  * Fields (like fetching field in update)

## 2. Packet descriptions
### TCP
  * Type (1 octet)
  * SM IP (4 octets)
  * SC IP (4 octets)
  * Payload
    * Open key exchange
      * Request or answer
      * Key Size (4 octets)
      * Key
    * Registration
      * User password (128 octets)
      * Method number
      * Methods
