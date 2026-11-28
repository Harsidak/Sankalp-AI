@echo off
if not exist out mkdir out
javac -cp "lib/*" -d out src/Main.java src/com/dao/*.java src/com/model/*.java src/com/util/*.java
if errorlevel 1 exit /b 1
java -cp "out;lib/*" Main
