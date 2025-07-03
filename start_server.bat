@echo off
cd /d "C:\Users\Skull\Desktop\blog"
echo Activando entorno y ejecutando servidor...
.\entorno\Scripts\activate && python manage.py runserver
