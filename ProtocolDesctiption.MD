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
```
	{
		Name : string,
		Fields : [Field]
	}
```
 
### 1.2 Script
```
	{
		Id : int,
		Name : string,
		Trigger : Trigger,
		Action : Action
	}
```

### 1.3 Trigger
```
	{
		Type : "VCH",
		DevId : int,
		FieldNme : string,
		ChangeType : string {"", ">", "<", "="},
		Value : Depends on value type
	}
	{
		Type : "AND",
		Trigger1 : Trigger,
		Trigger2 : Trigger
	}
```
 
### 1.4 Action
```
	{
		Type : "CHF",
		DevID : int,
		FieldName : string,
		Value : FieldValue
	}
	{
		Type : "MTH",
		MethodId : int,
		Fields : [FieldValue]
	}
```
  
### 1.5 FieldValue
```
	{
		Type : "VAL",
		Value : Depends on field type
	}
	{
		Type : "FLD",
		DevId : int,
		FieldName : string
	}
```

## 2. Packet descriptions
### 2.1
### TCP packet
1 SC connect to SD
```
	{
		Type : "SCC"
	}
```

