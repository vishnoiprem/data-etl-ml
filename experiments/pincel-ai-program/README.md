# Pincel AI Program — Computer Vision using PyTorch

> **A two-module Computer Vision course, taught the way I would teach
> it.** Module 1 is the foundations: convolutions, pooling, image
> processing. Module 2 is the architectures: LeNet, AlexNet, VGG,
> ResNet, Inception, DenseNet, EfficientNet, plus a human-action-recognition
> capstone.

This is a coursework directory, not a portfolio project. The PDFs and
notebooks inside are the slides and the hands-on material from a CV
program I ran. Use them to teach yourself, or to teach your team.

---

## Module 1 — Foundations

Six lessons, each one a slide deck and (where it makes sense) a
notebook. The progression is deliberate: a non-CS student can start
here and finish Module 2 in 8-10 weeks.

| # | Lesson | Format | What you'll be able to do |
|---|--------|--------|---------------------------|
| V1 | Course introduction + CV overview | PDF | Frame the field: classic CV vs. deep learning, where each wins |
| V2 | Image fundamentals | PDF | Explain an image as a tensor; channels, dtype, normalization |
| V3 | Convolution (the math) | PDF | Hand-derive the output shape of a conv layer; explain stride/padding |
| V4 | Image processing techniques | Jupyter | OpenCV + scikit-image: blur, edges, threshold, morphological ops |
| V5 | Convolution (the layers) | PDF | nn.Conv2d, kernel sizes, dilation, groups, depthwise conv |
| V6 | Pooling | PDF | Max / avg / global pooling; when to use each |

After Module 1 you should be able to read a CV paper's "method" section
and not get lost in the layer names.

---

## Module 2 — Architectures

Ten lessons, one architecture each (or one concept per lesson), plus
a human-action-recognition capstone. The slide-deck format is
deliberate: each one is a single idea, the math + the diagram + the
"why this matters in 2026" slide.

| # | Lesson | Architecture | The "one thing" you'll remember |
|---|--------|--------------|---------------------------------|
| V1 | Image classification journey | Timeline | The progression from hand-crafted features → deep nets → transformers |
| V2 | LeNet-5 | LeNet | The first CNN that worked; why it worked |
| V3 | (reserved) | — | — |
| V4 | AlexNet | AlexNet | ReLU + dropout + GPU = the deep-learning era begins |
| V5 | VGG | VGG | "Just stack 3x3 convs." The first time depth was the whole story |
| V6 | Transfer learning | VGG/ResNet as feature extractor | Why you almost never train from scratch on small data |
| V7 | Image augmentation | Data-side regularization | The cheap way to multiply your training set by 10x |
| V8 | GoogLeNet / Inception v1 | Inception | Multi-scale features in one layer; 12× fewer params than VGG |
| V9 | ResNet | ResNet | Skip connections: the trick that lets you stack 152 layers |
| V10 | DenseNet | DenseNet | Every layer reads from every previous layer; better gradient flow |
| V11 | EfficientNet | EfficientNet | Compound scaling: width × depth × resolution, jointly optimized |
| Capstone | Human Action Recognition | I3D / SlowFast | A real task: classify actions in video, not stills |

---

## Why this format

Three reasons I prefer slide-decks + notebooks over a textbook:

1. **One idea per lesson.** Each PDF is short. The student can finish
   one in 15 minutes, do the notebook, and move on. The accumulation
   matters more than any single lesson.
2. **Slides force clarity.** If I can't fit the architecture on one
   slide, I don't understand it. The constraint is the point.
3. **Notebooks are runnable.** A PDF of "ResNet explained" is 100
   pages; a notebook that loads ResNet, runs it on a sample image,
   and prints the top-5 predictions is 30 lines. The notebook teaches
   more in 5 minutes.

---

## Who this is for

- A working engineer who's heard of CV and wants a structured ramp.
- A student using this as a companion to a university CV course.
- A hiring manager who wants to see the way I teach.

It is **not** a research-level CV program. The latest architecture
covered is EfficientNet (2019). If you want ViT, Swin, ConvNeXt,
MAE, DINO, the post-2020 stuff — see
[`../ml/diffusion/`](../ml/diffusion/) for diffusion models and
[`../ai-engineering/`](../ai-engineering/) for the production
LLM/CV systems that build on this foundation.

---

## How to use this directory

```bash
# Pick a lesson
cd "pincel-ai-program/Computer Vision using PyTorch/Module 1"
open V1.pdf   # or: xdg-open V1.pdf on Linux

# Run a notebook (requires Jupyter + PyTorch)
cd "pincel-ai-program/Computer Vision using PyTorch/Module 1"
jupyter notebook V4_image_processing_techniques.ipynb

# For Module 2's capstone (Human Action Recognition)
cd "pincel-ai-program/Computer Vision using PyTorch/Module 2/Human Action Recognition"
ls
# The README inside has the dataset + training recipe
```

Each Module has a `notebooks/` subfolder if you want to write
your own code alongside the slides.

---

## Related directories

- [`../ml/`](../ml/) — The classical-ML and deep-learning half
  of the portfolio. The math, the implementations, the eval.
- [`../ai-engineering/`](../ai-engineering/) — Production LLM +
  CV systems. The "ship it" half that builds on these foundations.
- [`../ai-course-public/`](../ai-course-public/) — 197 lines,
  the broader AI engineering curriculum (not CV-specific).
