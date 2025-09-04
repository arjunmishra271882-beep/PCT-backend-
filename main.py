from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

app = FastAPI()

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        image = Image.open(io.BytesIO(await file.read()))
        # For now, just return a success message. Actual processing will be in /crop
        return {"filename": file.filename, "message": "Image uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error uploading image: {e}")

@app.post("/crop")
async def crop_image(
    file: UploadFile = File(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    rotate: int = Form(0),
    zoom: float = Form(1.0)
):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        original_width, original_height = image.size

        # Apply rotation
        if rotate != 0:
            image = image.rotate(rotate, expand=True)

        # Apply zoom (resizing for simplicity, actual zoom might be more complex)
        if zoom != 1.0:
            new_width = int(image.width * zoom)
            new_height = int(image.height * zoom)
            image = image.resize((new_width, new_height), Image.LANCZOS)

        # Calculate crop box based on the transformed image dimensions
        # The frontend should send coordinates relative to the *displayed* (potentially transformed) image
        # So, we can directly use x, y, width, height for cropping on the transformed image
        box = (x, y, x + width, y + height)
        cropped_image = image.crop(box)

        # Save cropped image to a bytes buffer
        img_byte_arr = io.BytesIO()
        # Determine format based on original file or always use PNG for transparency
        output_format = "PNG" if file.filename.lower().endswith(".png") else "JPEG"
        cropped_image.save(img_byte_arr, format=output_format)
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type=f"image/{output_format.lower()}")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {e}")


