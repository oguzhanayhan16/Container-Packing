import copy
import random
import numpy as np
import time


def defaultContainerMCTSPolicy(container):
    cont = True
    projectedContainer = copy.deepcopy(container)
    iteration = 0
    while cont:
        remaining = projectedContainer.getRemainingBoxes()
        print(f"Iteration {iteration}, Remaining boxes: {len(remaining)}")
        if len(remaining) > 0:
            box = remaining[0]
            print(f"Trying to add box {box.id} with dims ({box.dim1}, {box.dim2}, {box.dim3})")
            cont = projectedContainer.addBox(box)
            print(f"Add box result: {cont}")
        else:
            cont = False
        iteration += 1
    return projectedContainer


class ContainerMCTNode():
    def __init__(self, container, parent):
        self.container = container
        self.projectedContainer = container
        self.isLeaf = container.isFilled
        self.isFullyExpanded = self.isLeaf
        self.parent = parent
        self.visits = 0
        self.children = {}
        self.text = ""
        self.totalCBM = 0
        self.nodeCBM = 0


class ContainerMCTS():
    def __init__(self, container, maxIterations=None, explorationConstant=0, policy=defaultContainerMCTSPolicy):
        self.maxIterations = maxIterations
        self.explorationConstant = explorationConstant
        self.policy = policy
        self.container = container

    def fill(self):
        cnt = copy.deepcopy(self.container)
        self.root = ContainerMCTNode(cnt, None)
        self.root.text = "Root"

        for i in range(self.maxIterations):
            if not self.runIteration(i):
                print("All options tried.")
                break

        bestNode = self.getBestLeaf(self.root, explorationConstant=0)
        return bestNode

    def runIteration(self, ind):
        start = time.time()
        node = self.selectMCTNode(self.root)
        if node is not None:
            projectedContainer = self.policy(node.container)
            projectedCBM = projectedContainer.getCurrentCBM()
            node.projectedContainer = projectedContainer
            end = time.time()
            print("Ran iteration # %s  TTL:%.4f CBM (max:%.4f) in %.2f sec" % (
                ind, projectedCBM, self.root.totalCBM, (end - start)))
            self.registerTotalCBM(node, projectedCBM)
            return True
        else:
            return False

    def selectMCTNode(self, node):
        if not node.isLeaf:
            if node.isFullyExpanded:
                bestNode = self.getBestLeaf(node, self.explorationConstant)
                return self.selectMCTNode(bestNode)
            else:
                return self.expand(node)
        return node

    def expand(self, node):
        boxes = node.container.getRemainingBoxes()
        box_ids = list(boxes.keys())
        if not box_ids:
            return None
        while True:
            selected_id = random.choice(box_ids)
            box = boxes[selected_id]

            box_str = f"{box.id}xL:{box.dim1} H:{box.dim2} W:{box.dim3}"

            if box_str not in node.children:
                break
        newContainer = copy.deepcopy(node.container)
        result = newContainer.addBox(box)

        if result:
            newNode = ContainerMCTNode(newContainer, node)
            newNode.text = box_str
            newNode.boxConfig = box
            node.children[box_str] = newNode

            print(f"ADDED {box_str} to {node.text}, TTL:{len(newNode.container.addedBoxes)} TTL CBM:{newNode.container.getCurrentCBM()}")

            if len(boxes) == len(node.children):
                node.isFullyExpanded = True
                print(f"********** {node.text} FULLY EXPANDED")
            return newNode
        else:
            print(f"couldn't add {box}")
            node.isLeaf = True
            return None

    def getBestLeaf(self, node, explorationConstant):
        bestTotalCBM = float(0)
        bestNextLeaf = None

        for child in node.children.values():
            nodeCBM = child.totalCBM
            if nodeCBM >= bestTotalCBM:
                bestTotalCBM = nodeCBM
                bestNextLeaf = child

        if explorationConstant > 0:
            mode = np.random.uniform(0, 1)
            if mode < explorationConstant and len(node.children.values()) > 0:
                return random.choice(list(node.children.values()))
            else:
                return bestNextLeaf
        else:
            return bestNextLeaf

    def registerTotalCBM(self, node, totalCBM):
        while node is not None:
            node.visits += 1
            oldCBM = node.totalCBM
            node.totalCBM = max(node.totalCBM, totalCBM)
            print(f"Updating node '{node.text}': totalCBM {oldCBM} -> {node.totalCBM}")
            node = node.parent
