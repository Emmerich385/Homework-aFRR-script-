## Foreword

This script was made with the help of ChatGPT. I apologize in advance if this falls short from your expectations. I understand the principles of coding yet I lack sufficient knowledge to know all the neccessary commands by heart.

## Details of the script

The python script was written in Thonny. The script requests data from the Baltic Transparency Dashboard's website. The user can manually change the country and time period. The data consists of activated aFRR volumes and imbalance volumes. "Pandas" is used to convert the data to a dataframe. "Matplotlib" is used to plot a graph showing the activated aFRR volumes as positive and negative value bars according to upward and downward regulation, respectively, aswell as imbalanced volumes as a line.
Additionally, the script calculates descriptive statistics and correlations between aforementioned data which are displayed in shell.

## Results

The task was to analyse a specific date, 22.09.2025. Based on the graph, I noticed there might be a correlation between aFRR downward and imbalance volume, therefore I added the correlation calculations. My assumption was correct as Pearson r = 0.342. Furthermore, a negative correlation between aFRR upward and imbalance volume was noted (r = -0.208). I am cautious to conclude anything but I propose that on this particular day, unexpected fluctuations of balancing capacity occured which the automatic system was not equipped to handle, especially the down-regulation (I'm certain, though, that I lack detailed knowledge to back this claim). It would be interesting to know, whether the situation was handled by mFRR and if so, how exactly. 
Out of curiosity, I also added a time-lag correlation calculation but this yielded no remarkable results, supposedly due to the data being sampled by 15-minute intervals. Perhaps it would be a different case with a 0-5 minute lag calculation.
On a larger scale, I would actually like to understand how the calculations and corrections made in Baltic RCC translate to transmission machinery.
