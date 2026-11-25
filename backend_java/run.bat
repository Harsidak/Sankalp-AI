@echo off
rem Compiles every .java file in src into the out folder, then starts the program.
rem -cp "lib/*" = the classpath: where Java looks for ready-made classes (here: the MySQL driver jar).
if not exist out mkdir out
javac -cp "lib/*" -d out src/*.java
if errorlevel 1 exit /b 1
java -cp "out;lib/*" Main
