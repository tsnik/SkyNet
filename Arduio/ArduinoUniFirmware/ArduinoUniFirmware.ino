const int MaxAnalogPin = 5; //Magic number for Arduino Uno
const int MaxDigitalPin = 13; //Magic number for Arduino Uno
int del = 3000; //Delay between data packets
int prevtime;  //Time of prev data packet
String line = ""; //Line from pc is stored here

void setup() {
  Serial.begin(1200);
  prevtime = millis();
}
void loop() {
  sendData();
  receiveData();
}

void sendData()
{
  int curtime = millis();
  int diff = curtime - prevtime;
  if (diff<0)
  {
    diff = curtime;
    prevtime = 0;
  }
  if (diff > del)
  {
    for(int i = 0; i <= MaxAnalogPin; i++)
    {
      int sensorValue = analogRead(i);
      Serial.print("A");
      Serial.print(i);
      Serial.print(":");
      Serial.print(sensorValue);
      Serial.print("\n");
    }
    for(int i = 0; i <= MaxDigitalPin; i++)
    {
      int sensorValue = digitalRead(i);
      Serial.print(i);
      Serial.print(":");
      Serial.print(sensorValue);
      Serial.print("\n");
    }
    prevtime = curtime;
  }
}

void receiveData()
{
  if(getLine() != -1)
  {
    int div_index = line.indexOf(':');
    int pin = line.substring(0, div_index).toInt();
    int value = line.substring(div_index + 1).toInt();
    pinMode(pin, OUTPUT);
    line = "";
    if(value == 0)
    {
      digitalWrite(pin, LOW);
    }
    else
    {
      digitalWrite(pin, HIGH);
    }
  }
}

int getLine()
{
  while(Serial.peek()!=-1)
  {
    int inbyte = Serial.read();
    if(inbyte == '\n')
    {
      return line.length();
    }
    line += (char)inbyte;
  }
  return -1;
}


