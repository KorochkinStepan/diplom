## HOW TO DEPLOY


### SERVER
1. - change .env <br>
2. - ```docker-compose -f docker-elastic.yaml ``` <br>
3. - go to ```"http://localhost:5601/"``` <br>
4. - set up kibana by passing elastic adress ("http://elastic:9200/") <br>
5. - dashboards -> import -> load "Dashboard.ndjson" <br>
DONE! <br>

<br><br>
### USER
1. - get client.exe from https://disk.yandex.ru/d/ndkyOuTZ9vIBWw (or build it by  ```"pyinstaller --onefile core/client.py"```) <br>
2. - install NSSM (https://www.nssm.cc/download) <br>
3. - ```nssm.exe install ProjectService ``` <br>
    ```nssm.exe set ProjectService Application "c:\path\to\client.exe"``` <br>
    ```nssm.exe set ProjectService AppParameters "c:\path\to\project\app\client.py"``` <br>
4.   to start the service  = ```nssm.exe start ProjectService ```<br>
    to stop the service = ```nssm.exe stop ProjectService``` <br>
