#!/usr/bin/env python
"""
Plot the result of all algorithms for the same problem.

First problem was inter-arrival distribution Uniform(60, 75) and time-lag Normal(57.01, 6.66). This leads to very
limited overlaps of events.

Second problem was inter-arrival distribution Uniform(5, 55) and time-lag Normal(77.01, 6.66). This leads to many
overlaps of events.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# no overlap
true = stats.norm(57.01, 6.66)
lagem = stats.norm(56.044279071161796, 6.362708854320515)
marco = stats.norm(56.7426443784014, 6.901419693576198)
munkres = stats.norm(57.35554344112395, 6.552604159986489)

x = np.linspace(25, 95, 10000)
yTrue = true.pdf(x)
yLagem = lagem.pdf(x)
yMarco = marco.pdf(x)
yMunkres = munkres.pdf(x)

plt.plot(x, yTrue, label="True distribution", color="r")
plt.plot(x, yLagem, label="lagEM", color="b")
plt.plot(x, yMarco, label="MarcoMatcher", color="g")
plt.plot(x, yMunkres, label="MunkresMatcher", color="y")
plt.legend()
plt.figure()

# overlap
true = stats.norm(77.01, 6.66)
lagem = stats.norm(77.69708117865822, 5.688293861445452)
marco = stats.norm(77.18212977062922, 6.157629697647032)
munkres = stats.norm(76.80436865501531, 6.778075732258937)

x = np.linspace(50, 110, 10000)
yTrue = true.pdf(x)
yLagem = lagem.pdf(x)
yMarco = marco.pdf(x)
yMunkres = munkres.pdf(x)

plt.plot(x, yTrue, label="True distribution", color="r")
plt.plot(x, yLagem, label="lagEM", color="b")
plt.plot(x, yMarco, label="MarcoMatcher", color="g")
plt.plot(x, yMunkres, label="MunkresMatcher", color="y")
plt.legend()
plt.figure()


barWidth = 0.35

timeLagEm = np.array([118250, 140413, 103702, 152488, 121212])
timeMunkres = np.array([313, 337, 332, 365, 571])
timeMarco = np.array([27558, 23367, 16036, 17506, 15420, 15630, 15558])

plt.bar(1, timeLagEm.mean() / 1000, barWidth, label="lagEM", color="b")
plt.bar(1.5, timeMarco.mean() / 1000, barWidth, label="MarcoMatcher", color="g")
plt.bar(2, timeMunkres.mean() / 1000, barWidth, label="MunkresMatcher", color="y")
plt.legend()
plt.gca().get_xaxis().set_visible(False)
plt.ylabel("Avg. Runtime in Seconds")
plt.show()


