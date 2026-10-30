# As AI Lead, How I Guided Data Labeling Quality

When people ask me what I actually did day-to-day as Head of AI, they usually expect me to talk about model architectures or GPU clusters. The honest answer is more boring and more important: I spent most of my time worrying about labels. Not the models. The labels.

Every team I've ever led eventually learned the same lesson the hard way. A model that looked great in evaluation would fall apart in production, and when we traced it back, the culprit was almost never the algorithm. It was the data. Specifically, it was three or four labelers quietly disagreeing on what "high-risk transaction" meant, or a guideline that said "flag suspicious product listings" without defining suspicious. The math was fine. The ground truth was the problem.

So my job, more than anything else, was to make sure the ground truth was actually true.

## Starting with the guideline, not the tool

The first thing I changed when I joined my last team was the order in which we approached labeling projects. Most teams I've inherited start by picking a tool — Labelbox, SuperAnnotate, Scale, CVAT, whatever — and then writing guidelines to fit the tool. I do the opposite. I make the team write a one-page guideline before we even look at platforms, and that page has to survive a brutal test: if I hand it to three new labelers and have them annotate the same fifty samples blind, do they agree?

The first time we ran this exercise on a banking fraud project, our inter-annotator agreement was around 61%. That number tells you everything. It meant nearly four out of every ten labels in our training set were essentially a coin flip. We hadn't trained a fraud model yet, but I already knew it would underperform. We rewrote the guideline three times before the agreement crossed 90%. Only then did we start labeling at scale. That habit alone — refusing to scale before the guideline is stable — has probably saved more model performance than any other single decision I've made.

## The two industries that taught me the most

I've worked across enough sectors to see that data labeling problems look very different depending on what you're trying to learn. The two that shaped my thinking most are banking and e-commerce, and they're almost mirror images of each other.

In banking, the labels are sparse and the cost of getting them wrong is enormous. A fraud detection system might see a million transactions a week and only a few hundred are actually fraud. The class imbalance is brutal, the ground truth comes in slowly (chargebacks can take 60 to 120 days to materialize), and a single false negative can mean a regulator phone call. What this taught me is that quality in banking labeling isn't really about volume — it's about confidence. We used multi-reviewer setups for every fraud label, and for the borderline cases we built what I called the "second opinion" workflow, where a senior analyst had to confirm anything the first labeler marked as ambiguous. We also kept a deliberately small but extremely clean gold set — about 2,000 transactions hand-labeled by our most experienced fraud analyst — that we used to evaluate everything, including the labelers themselves.

E-commerce is the opposite problem. The data is overwhelming, the labels are subjective, and you can drown in volume long before you achieve quality. When I led labeling for a product catalog enrichment project — the kind where you tag color, material, style, occasion, fit — we had millions of items and dozens of attributes per item. There's no way to label that manually. So we built what's now pretty standard in 2026 but felt experimental at the time: a model-in-the-loop pipeline. A pre-trained model would propose labels, humans would only review the ones the model wasn't confident about, and a separate auditor would sample the rest. This let us scale to hundreds of thousands of labels per week while keeping the human reviewers focused on the genuinely hard cases. The labelers, frankly, were happier too — they weren't drawing the same bounding box for the thousandth time.

## What I actually measured

There's a version of this conversation that ends at "we measured accuracy." I don't trust that answer when I hear it from candidates I interview, because accuracy alone hides too much. What I actually tracked, every week, was four things.

The first was inter-annotator agreement, broken down by label class. A blended IAA number is almost useless; what matters is which specific labels people disagree about, because those are the labels the model will struggle with. The second was gold-set accuracy per labeler — we'd quietly inject items from our trusted gold set into normal work batches and track each labeler's performance over time. The third was rework rate, meaning the percentage of labels that had to be corrected on a second pass. This is the single best leading indicator of guideline quality I've ever found. If rework spikes, your guideline is broken, not your people. And the fourth was time-to-resolve for edge cases — how quickly we could update the guideline and propagate the fix when a labeler raised a question. Slow resolution times mean labelers are guessing, and guessing means inconsistency.

## The shift since 2025

The thing I'd tell anyone leading data labeling today is that the field has changed more in the last 18 months than in the previous five years, and it's because of LLMs. The whole industry has moved from "label everything" to "label the right things." When you can use a foundation model to pre-label, the human's job stops being annotation and starts being arbitration. The people you want are no longer fast clickers — they're domain experts who can resolve genuinely ambiguous cases that the model couldn't.

I saw a stat recently that vendors were charging up to $100 per high-quality RLHF comparison in late 2025. That's a different economy than the old crowdsourcing model where labels cost cents. The work is more skilled, more expensive, and more important. I've adjusted accordingly. On my last team, we cut our overall labeling volume by roughly 70% but tripled the spend per labeled example, and the model performance went up, not down. The lesson is that better data beats more data, almost every time.

This also changes how I hire. Five years ago I'd look for labeling vendors with the biggest workforce. Now I look for vendors who can give me a small, stable, domain-trained team that stays with the project long enough to build real expertise. In banking, that means analysts who actually understand chargeback patterns. In e-commerce, that means people who know the difference between a "midi" and a "tea-length" dress without me having to explain it.

## What I'd say to anyone starting out

If you're stepping into an AI lead role and you're inheriting a labeling operation, the single most useful thing you can do in your first month is sit with three labelers for a full day and watch them work. Don't bring an agenda. Just watch. You will find at least one place where the guideline is wrong, one place where the tool is slowing them down, and one place where they've been quietly making the same judgment call differently every time. Fix those three things and you'll have done more for model quality than a quarter of architecture work.

Data labeling looks unglamorous from the outside. Inside the work, it's where every AI system either earns its credibility or quietly loses it. That's why I gave it most of my attention as a lead, and why I'd do it again.
