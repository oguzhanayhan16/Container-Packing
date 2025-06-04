from enum import Enum
import numpy as np
import math
import copy
import random

from ContainerPacking.Packing.Porperties.Item import Item


class Container:
    def __init__(self, container_id, length, width, height, boxes=None,
                 spaceOptimizationFactor=1, useDeepSearch=False,
                 ):

        # Temel bilgiler
        self.id = container_id
        self.length = length
        self.width = width
        self.height = height
        self._volume = length * width * height

        # EB-AFit / MCTS için gerekli bilgiler
        self.boxes = {box.id: box for box in boxes} if boxes else {}

        self.remainingBoxes = copy.deepcopy(self.boxes)
        self.addedBoxes = {}
        self.addedBoxLocations = {}

        self.spaceOptimizationFactor = spaceOptimizationFactor
        self.useDeepSearch = useDeepSearch
        self.isFilled = False

        self.nextEmptySpace = {"z": 0, "y": 0, "x": 0}
        self.nextNeighborSpaces = {"right": None, "top": None, "front": None}
        self.minHeightAtRow = 0
        self.minLengthAtRow = 0
        self.totalVolume = 0.0

        self.scaledDimensions = {
            "length": int(length),
            "height": int(height),
            "width": int(width)
        }

        self.dimensions = np.zeros(
            (self.scaledDimensions["length"],
             self.scaledDimensions["height"],
             self.scaledDimensions["width"]),
            dtype=bool
        )

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = value

    def getContainerCBM(self):
        cbm = self.length * self.width * self.height
        return cbm  # <<< Burası    

    def getCurrentCBM(self):
        return self.totalVolume  # <<< Burası

    def getRemainingBoxes(self):
        return self.remainingBoxes

    def addBox(self, box):
        length, height, width = self.scaledDimensions["length"], self.scaledDimensions["height"], self.scaledDimensions[
            "width"]
        blockLength = math.ceil(box.dim1 / self.spaceOptimizationFactor)
        blockHeight = math.ceil(box.dim2 / self.spaceOptimizationFactor)
        blockWidth = math.ceil(box.dim3 / self.spaceOptimizationFactor)
    
        for i in range(self.nextEmptySpace["z"], length):
            print(f"  → Checking depth z={i} for Box {box.id} with dims=({blockLength}, {blockHeight}, {blockWidth})")
            for j in range(self.nextEmptySpace["y"], height):
                for k in range(self.nextEmptySpace["x"], width):
                    doesFit = True

                    if i + blockLength > length or j + blockHeight > height or k + blockWidth > width:
                        doesFit = False
                    else:
                        for p in range(1, blockLength + 1):
                            for r in range(1, blockHeight + 1):
                                for s in range(1, blockWidth + 1):
                                    if self.dimensions[i + p - 1, j + r - 1, k + s - 1]:
                                        doesFit = False

                    if doesFit:
                        self.addedBoxes[box.id] = box
                        self.remainingBoxes.pop(box.id, None)
                        self.addedBoxLocations[box.id] = {"z": i, "y": j, "x": k}
                        self.totalVolume += getattr(box, 'volume', box.dim1 * box.dim2 * box.dim3)

                        if self.minHeightAtRow is None:
                            self.minHeightAtRow = blockHeight + j
                        else:
                            self.minHeightAtRow = min(self.minHeightAtRow, blockHeight + j)

                        if self.minLengthAtRow is None:
                            self.minLengthAtRow = blockLength + i
                        else:
                            self.minLengthAtRow = min(self.minLengthAtRow, blockLength + i)

                        self.dimensions[i:i + blockLength, j:j + blockHeight, k:k + blockWidth] = True

                        self.mapNeighborSpacesAfterBox(
                            blockLength=blockLength,
                            blockHeight=blockHeight,
                            blockWidth=blockWidth,
                            currentLength=i,
                            currentHeight=j,
                            currentWidth=k
                        )

                        self.nextEmptySpace = self.nextNeighborSpaces["right"]
                        self.nextNeighborSpaces["right"] = None

                        box.is_packed = True
                        print(f"✅ Box {box.id} placed at ({i},{j},{k})")
                        return True

            # Satır sonunda yukarı çıkmayı dene
            if self.nextNeighborSpaces["top"]:
                self.nextEmptySpace = self.nextNeighborSpaces["top"]
                self.nextNeighborSpaces["top"] = None
                print(f"↪ Box {box.id} going up row to {self.nextEmptySpace}")
                return self.addBox(box)

        # Derinlik boyunca ilerlemeyi dene
        if self.nextNeighborSpaces["front"]:
            self.nextEmptySpace = self.nextNeighborSpaces["front"]
            self.minHeightAtRow = 0
            self.nextNeighborSpaces["front"] = None
            print(f"↪ Box {box.id} coming forward to {self.nextEmptySpace}")
            return self.addBox(box)

        # Kutuyu yerleştirecek yer kalmadı
        self.isFilled = True
        print(f"❌ Box {box.id} could not be placed. Container might be full.")
        return False

    def mapNeighborSpacesAfterBox(self, blockLength, blockWidth, blockHeight, currentLength, currentWidth,
                                  currentHeight):
        if currentWidth + blockWidth <= self.scaledDimensions["width"]:
            self.nextNeighborSpaces["right"] = {
                **self.nextEmptySpace,
                "x": currentWidth + blockWidth
            }
        if currentHeight + blockHeight <= self.scaledDimensions["height"]:
            y = currentHeight + blockHeight
            if self.useDeepSearch:
                y = min(y, self.minHeightAtRow)
            self.nextNeighborSpaces["top"] = {
                "x": 0, "y": y, "z": self.nextEmptySpace["z"]
            }
        if currentLength + blockLength <= self.scaledDimensions["length"]:
            z = currentLength + blockLength
            if self.useDeepSearch:
                z = min(z, self.minLengthAtRow)
            self.nextNeighborSpaces["front"] = {
                "x": 0, "y": 0, "z": z
            }

    def getResultsJSON(self):
        outBoxes = [
            {"box": self.addedBoxes[box_id], "location": self.addedBoxLocations[box_id]}
            for box_id in self.addedBoxes
        ]
        return {
            "boxes": outBoxes,
            "cbm": self.getCurrentCBM(),
            "containerCBM": self.getContainerCBM(),
            "dimensions": {
                "length": self.length,
                "width": self.width,
                "height": self.height
            },
            "scaledDimensions": self.scaledDimensions,
            "spaceOptimizationFactor": self.spaceOptimizationFactor,
            "usedDeepSearch": self.useDeepSearch
        }
