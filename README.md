## COMANDOS GIT PRINCIPALES

* **Hacer un commit nuevo** 

  ```bash
  git add .
  git commit -m "mensaje"
  ```
* **Crear un branch nuevo**

  ```bash
  git checkout -b nombre_branch
  ```

* **Cambiar de branch**

  ```bash
  git checkout nombre_branch
  ```

* **Borrar un branch local**

  ```bash
  git branch -d nombre_branch
  ```

* **Hacer merge de otra branch a la actual**

  ```bash
  git merge nombre_branch
  ```

* **Subir cambios al remoto**

  ```bash
  git push origin nombre_branch
  ```

* **Traer cambios del remoto y mezclarlos**

  ```bash
  git fetch   
  git pull origin main
  ```
Git fetch es el comando que le dice a tu git local que recupere la última información de los metadatos del original (aunque no hace ninguna transferencia de archivos. Es más bien como comprobar si hay algún cambio disponible). 
Se recomienda hacer siempre un git fetch antes de un git pull y también antes de un push para saber si alguien más no hizo un Push antes y evitar problemas.

* **Ver el estado de los archivos**

  ```bash
  git status
  ```


### OTROS COMANDOS
## 🔹 **Commit & cambios**

* **Modificar el último commit (mensaje y/o archivos)**

  ```bash
  git commit --amend
  ```

* **Borrar el último commit pero mantener los cambios en el working directory**

  ```bash
  git reset --soft HEAD~1
  ```

* **Borrar el último commit y los cambios también**

  ```bash
  git reset --hard HEAD~1
  ```
---

## 🔹 **Merge & sincronización**

* **Forzar que el remoto sobrescriba lo local**

  ```bash
  git fetch origin
  git reset --hard origin/main
  ```

* **Forzar que lo local sobrescriba lo remoto** 

  ```bash
  git push origin main --force
  ```

---

## 🔹 **Estado & utilidad**


* **Ver historial de commits**

  ```bash
  git log --oneline --graph --decorate --all
  ```

* **Ver a qué remoto apunta tu repo**

  ```bash
  git remote -v
  ```

---

## FLUJO NORMAL QUE SIGO PARA HACER UN CRUD 
0)  **Crear la tabla en la BD**
1)  **Crear en "Schemas" un archivo "nombre.py" con los modelos Pydantic (Create - Update - Out)**
2)  **Ir a "Services" y crear un archivo "nombreServices.py" con cada una de las funciones que se encargaran del CRUD**
3)  **Crear en "routes" un archivo "nombreRoutes.py" con cada uno de los endpoints que consumen las funciones del controlador**
4)  **Agregar las rutas en el main.py**
5)  **Probar los endpoints con Postman o la documentación automática de FastAPI**

**ACLARACIONES:** 
* Puede que a futuro cambiemos debamos separar Service en Service y Controllers. HAY QUE PREGUNTARLE AL PROFE.
* No se olviden de comentar el código, siempre que vean algo que no entiendan o descubran algo nuevo dejenlo ahí documentado.
* SIEMPRE AVISAR CUANDO ESTÉN POR HACER UN PUSH Y SIEMPRE VERIFICAR SI ESTÁN AL DÍA CON EL REPOSITORIO REMOTO
* No se olviden de crear el archivo .env y agregar los datos que le competen, ya que eso no se exporta al github.
* Verifiquen que tengan todas las dependencias y bibliotecas del requirements.txt
* Puede crear un solo endpoint y probarlo y así con el resto, en lugar de hacer todos y probarlos juntos.
