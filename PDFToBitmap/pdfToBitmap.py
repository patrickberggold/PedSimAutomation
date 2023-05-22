import io
from pdf2image import convert_from_path
from PIL import Image

# Convert PDF to a list of PIL Image objects
pdf_images = convert_from_path('./sample.pdf')

# Open the first page as a PIL Image object
first_page = pdf_images[0]

# Convert the first page to a bitmap
bitmap_image = first_page.convert('1')

bitmap_image.save('sample.bmp', 'BMP')

# # Create an in-memory file object
# image_buffer = io.BytesIO()

# # Save the bitmap image to the in-memory file object
# bitmap_image.save(image_buffer, format='BMP')

# # Rewind the buffer to the beginning
# image_buffer.seek(0)

# # You can now use the image_buffer as needed, for example:
# # image_buffer.save('image.bmp')

# # Optionally, if you want to load the bitmap image from the buffer
# loaded_bitmap = Image.open(image_buffer)
# loaded_bitmap.show()
