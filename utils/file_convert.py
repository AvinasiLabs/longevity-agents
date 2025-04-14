import io
import img2pdf


def to_pdf(img:bytes):
    """Convert a image into pdf format.

    Args:
        img (bytes): Image bytes.
    """
    return img2pdf.convert(io.BytesIO(img))
    

if __name__ == '__main__':
    ...