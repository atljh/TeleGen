from PIL import Image

def is_image_valid(path: str) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False

if is_image_valid("draper.jpg"):
    print("Изображение нормальное")
else:
    print("Изображение битое")
