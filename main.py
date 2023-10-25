import glob
import os
import detector as det
from multiprocessing import Pool


# multiprocessing module to process images concurrently
def process_image(image):
    try:
        result = det.objDetector(image)
        return result
    except Exception as e:
        print(f"Could not detect for {image}: {str(e)}")
        return None


if __name__ == "__main__":
    image_files = (
        glob.glob("Testing/*.png")
        + glob.glob("Testing/*.jpg")
        + glob.glob("Testing/*.jpeg")
    )

    with Pool(processes=4) as pool:  # Adjust the number of processes as needed
        results = pool.map(process_image, image_files)

    for i, result in enumerate(results):
        if result is not None:
            print(f"Processing Image {i + 1} Done: {image_files[i]}")
