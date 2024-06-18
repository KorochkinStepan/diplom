HOW TO DEPLOY


SERVER
1 - change .env
2 - docker-compose -f docker-elastic.yaml 
3 - go to "http://localhost:5601/"
4 - set up kibana by passing elastic adress ("http://elastic:9200/")
5 - dashboards -> import -> load "Dashboard.ndjson"
DONE!


USER
1 - get client.exe from https://disk.yandex.ru/d/ndkyOuTZ9vIBWw (or build it by "pyinstaller --onefile core/client.py")
2 - install NSSM (https://www.nssm.cc/download)
3 - nssm.exe install ProjectService 
    nssm.exe set ProjectService Application "c:\path\to\client.exe"
    nssm.exe set ProjectService AppParameters "c:\path\to\project\app\client.py"
4   ```to start the service  = nssm.exe start ProjectService ```
   ``` to stop the service = nssm.exe stop ProjectService```
