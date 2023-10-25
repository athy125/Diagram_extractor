import cv2 as cv
import numpy as np
import os
import glob
from multiprocessing import Pool

# Use try-except blocks to handle the possibility of no matching files.
try:
    modelConfigFile = glob.glob("*.cfg")[0]
except IndexError:
    print("No configuration files found.")
    exit()

print("CFG File:", modelConfigFile)

try:
    modelWeights = glob.glob("*.weights")[0]
except IndexError:
    print("No weight files found.")
    exit()

print("Weights File:", modelWeights)

confidenceThreshold = 0.25
nmsThreshold = 0.40
inpWidth = 416
inpHeight = 416
classes = ["object"]

# Setup Deep Learning Model
net = cv.dnn.readNetFromDarknet(modelConfigFile, modelWeights)
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)
print("----------- CFG & Weights File Loaded. -----------")


def getOutputNames(net):
    layerNames = net.getLayerNames()
    return [layerNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]


def drawPred(classId, conf, left, top, right, bottom, frame):
    cv.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
    label = "%.2f" % conf
    if classes:
        assert classId < len(classes)
        label = "%s:%s" % (classes[classId], label)
    labelSize, baseLine = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    cv.putText(frame, label, (left, top), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))


def postProcess(frame, outs):
    frameHeight = frame.shape[0]
    frameWidth = frame.shape[1]

    classIds = []
    confidences = []
    boxes = []
    frames = []

    for out in outs:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]

            if confidence > confidenceThreshold:
                center_x = int(detection[0] * frameWidth)
                center_y = int(detection[1] * frameHeight)
                width = int(detection[2] * frameWidth)
                height = int(detection[3] * frameHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    indices = cv.dnn.NMSBoxes(boxes, confidences, confidenceThreshold, nmsThreshold)

    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        drawPred(
            classIds[i], confidences[i], left, top, left + width, top + height, frame
        )
        frames.append(frame[top : top + height, left : left + width])

    return frames


def process_image(image):
    try:
        name = os.path.splitext(os.path.basename(image))[0]
        cap = cv.imread(image)
        blob = cv.dnn.blobFromImage(
            cap, 1 / 255, (inpWidth, inpHeight), (0, 0, 0), True, crop=False
        )
        net.setInput(blob)
        outs = net.forward(getOutputNames(net))
        frames = postProcess(cap, outs)

        if len(frames) > 0:
            t, _ = net.getPerfProfile()
            label = "Inference time: %.2f ms" % (t * 1000.0 / cv.getTickFrequency())
            print(f"Processed: {name}, {label}")
            count = 0
            for detection in frames:
                cv.imwrite(f"Output/{count}_{name}.jpg", detection)
                count += 1
    except Exception as e:
        print(f"Could not detect for {image}: {str(e)}")


if __name__ == "__main__":
    image_files = (
        glob.glob("Testing/*.png")
        + glob.glob("Testing/*.jpg")
        + glob.glob("Testing/*.jpeg")
    )

    with Pool(processes=4) as pool:
        pool.map(process_image, image_files)
