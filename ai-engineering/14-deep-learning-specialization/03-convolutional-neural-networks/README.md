# Course 3 — Convolutional Neural Networks

> **Instructor:** Andrew Ng · **Level:** Intermediate · **Time:** 4 weeks

The vision track. From a single conv layer to ResNet-152. From image classification to object detection to face recognition to neural style transfer. CNNs are still the workhorse of vision — and the basis of ViT (Module 15 of the AI Engineering course).

---

## What you'll learn

```
   CONVOLUTION                     POOOLING                ARCHITECTURES
   ───────────                     ───────                 ─────────────
   What a filter is                Max pool                LeNet-5
   How stride works                Average pool            AlexNet
   Padding (same vs valid)         Global avg pool         VGG
   Receptive fields                Adaptive pool           ResNet
   Multi-channel (RGB)                                   Inception
   1×1 convolutions                                    MobileNet
```

---

## Week 1 — Foundations of CNNs

**Topics:**
- Edge detection example
- Padding, stride, convolution operations
- 3D convolutions on RGB
- One layer of a CNN (CONV → RELU → POOL)
- Simple ConvNet example (LeNet-style)
- Pooling layers
- CNN example (the architecture pattern)

**The big idea:** Convolution exploits the structure of images — local connectivity, parameter sharing, translation equivariance. A conv layer has 100-1000× fewer parameters than a dense layer with the same receptive field.

---

## Week 2 — Deep convolutional models

**Topics:**
- Classic architectures: LeNet, AlexNet, VGG
- ResNets and skip connections
- Why ResNets work
- Networks in networks and 1×1 convolutions
- Inception architecture
- Transfer learning
- Data augmentation

**The big idea:** Deeper isn't always better — until you add skip connections. ResNets opened the door to 100+ layer networks. Inception & 1×1 convolutions let you mix channel widths efficiently.

---

## Week 3 — Object detection

**Topics:**
- Object localization
- Landmark detection
- Object detection (sliding windows)
- Convolutional implementation of sliding windows
- Bounding box predictions (YOLO algorithm)
- Intersection over union (IoU)
- Non-max suppression
- Anchor boxes

**The big idea:** Object detection = classification + localization. YOLO (You Only Look Once) revolutionized this by treating detection as a single regression problem.

---

## Week 4 — Special applications

**Topics:**
- Face recognition (one-shot learning, Siamese networks, triplet loss)
- Neural style transfer
- What are deep ConvNets learning (visualization)
- Various architectures: MobileNet, EfficientNet, etc.

**The big idea:** Face recognition = "is this the same person?" not "who is this?" That's a Siamese network with a contrastive/triplet loss. Neural style transfer = "this content + this style = a new image."

---

## Lead lesson

See `01-building-a-cnn-from-scratch.md` for the full worked example: build a CNN in NumPy (forward pass only, for intuition), then build and train the real one in PyTorch on CIFAR-10, hitting 75% accuracy.