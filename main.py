import asyncio
import os
import random
import string

import jinja2
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="files")
app.secret_key = os.getenv("SKEY", "secret")


async def delete_file_after_delay(file_path, delay):
    await asyncio.sleep(delay)

    async def de():
        print(f"Deleting file {file_path}")
        os.remove(file_path)

    await de()


def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


@app.get("/")
def index():
    return {"message": "Redirect to...", "url": "https://satya.devh.in/"}


@app.get("/f/{path}")
async def f(request: Request, path: str, p: str, download: int = 0):
    try:
        if download == 1:
            return FileResponse(f"files/{path}_{p}", media_type="application/octet-stream", filename=f"{p}")
        return templates.TemplateResponse(f"{path}_{p}", {"request": request})
    except jinja2.exceptions.TemplateNotFound:
        return templates.TemplateResponse("404.html", {"request": request})
    except Exception as e:
        dl_link = "/f/{}?p={}&download=1".format(path, p)
        return templates.TemplateResponse("500.html", {"request": request, "dl_link": str(dl_link)})


@app.post("/d/d/upl")
async def u_p_l(background_tasks: BackgroundTasks, file: UploadFile = File(...), ):
    try:
        # Check file size
        max_file_size = 10 * 1024 * 1024  # 10MB
        file_size = file.file.seek(0, os.SEEK_END)
        if file_size > max_file_size:
            return HTTPException(status_code=400, detail="File size exceeds the maximum limit (10MB)")

        if not file:
            return HTTPException(status_code=400, detail="No file uploaded")

        if file.filename.endswith(('.html', '.htm')):
            random_name = generate_random_string(10)
            file_path = f"files/{random_name}_{file.filename}"
            with open(file_path, "wb") as f:
                contents = await file.read()
                f.write(contents)

            # Schedule file deletion after 12 hours
            deletion_delay = 12 * 60 * 60  # 12 hours
            background_tasks.add_task(delete_file_after_delay, file_path, deletion_delay)

            return {
                "message": "File uploaded successfully",
                "link": f"/f/{random_name}?p={file.filename}",
                "download": f"/f/{random_name}?p={file.filename}&download=1",
                "detail": "The link will expire after 12 hours",

            }

        else:
            return HTTPException(status_code=400, detail="Invalid file format. Only HTML files are allowed")
    except Exception as e:
        return HTTPException(status_code=500, detail="An error occurred while uploading the file: {}".format(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=os.getenv("PORT", 5000), reload=True)
