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
Every packet has to have field "reqid":
* Request - RQ + uniq id
* Response - Re + same id as was in request

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
### 3.3 TCP packet

3 Field change  
```
{
	Type : "FCH",
	SDIP : string,
	DevId : int,
	Field : Field
}
```

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
		MethodId : int,
		SD : SD,
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
		Value : FieldValue
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
		Type : "LFV",
		DevId : int,
		FieldName : string
	}
	{
		Type : "RFV",
		DevId: int,
		FieldName : string
	}
```

### 1.6 SD
```
	{
		IP : string,
		Name : string
	}
```

### 1.7 Device  
```
{  
	ID : int,  
	Name : string,  
	Fields : [Field],
	SD : SD
}
```

### 1.8 Field
```
{
	Name : string,
	Type : int,
	Writable : bool,
	Value : as Type
}
```

## 2. Packet descriptions
### 2.1 Packet types
1. SCM - SC connect to SM
2. GDL - Get device list
3. GDF - Get device fields
4. UDF - Update device fields
5. SSD - Search SD
6. RSD - Register SD
7. RND - Rename Device
8. GMT - Get methods
9. GSC - Get scripts
10. CSC - Create script
11. ESC - Edit script
11. DSC - Delete script
12. CMT - Call method (The only request sent from SM to SC)

In packets 5 - 12 SC should also pass Password (Special admin password)

### 2.2 TCP packet
1 SC connect to SM
 * Request
```
	{
		Type : "SCM",
		Password : string,
		Methods : [Method],
		Name : string
	}
```
  * Response
```
	{
		Type : "SCM",
		Result : "OK",
		Name : string
	}
```

2 Get device list
* Request
```
	{
		Type : "GDL"
	}
```
* Response
```
	{
		Type : "GDL"
		Devices : [Device]
	}
```

3 Get device fields
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
4 Update device field
* Request
```
	{
		Type : "UDF",
		DevId : int,
		FieldName : string,
		Value : depends on field type
	}
```
* Reponse
```
	{
		Type : "UDF",
		DevId : int,
		Field : Field
	}
```

5 Search SD
* Request
```
	{
		Type : "SSD"
	}
```
* Response
```
	{
		Type : "SSD",
		Servers : [SD]
	}
```

6 Register SD
* Request
```
	{
		Type : "RSD",
		IP : string,
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

7 Rename device
* Request
```
	{
		Type : "RND",
		DevId : int,
		Name : string
	}
```
* Response
```
	{
		Type : "RND",
		Device : Device
	}
```

8 Get methods
* Request
```
	{
		Type : "GMT"	
	}
```
* Response
```
	{
		Type : "GMT",
		Methods : [Method]
	}
```

9 Get scripts

9.1 All scripts
* Request
```
	{
		Type : "GSC"
	}
```
* Response
```
	{
		Type : "GSC",
		Scripts : [Script]
	}
```
9.2 Script by id
* Request
```
	{
		Type : "GSC",
		ScriptId : int
	}
```
* Response
```
	{
		Type : "GSC",
		Script : Script
	}
```
10 Create script
* Request
```
	{
		Type : "CSC",
		Script : Script
	}
```
* Response
```
	{
		Type : "CSC",
		Script : Script
	}
```

11 Edit script
* Request
```
	{
		Type : "CSC",
		Script : Script
	}
```
* Response
```
	{
		Type : "CSC",
		Script : Script
	}
```

12 Delete script
* Request
```
	{
		Type : "DSC",
		ScriptId : int
	}
```
* Response
```
	{
		Type : "DSC",
		ScriptId : int,
		Status : "DELETED"
	}
```

13 Call method
* Request
```
	{
		Type : "CMT",
		Method : Method
	}
```
* Response
```
	{
		Type : "CMT",
		Status : "EXECUTED"
	}
```
