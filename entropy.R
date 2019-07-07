library(ggplot2)

d <- read.csv('morphosyntactic_entropy.csv')
d$Language <- factor(d$Language,
                     levels = c('French', 'Russian', 'Czech', 'Arabic'
                                'Japanese', 'Chinese', 'Indonesian'))
limits <- aes(
    ymax = d$CI_upper,
    ymin = d$CI_lower)

png('morphosyntactic_entropies_pud_vs_native.png',
    width = 16,
    height = 10,
    units = 'in',
    res = 300)
p <- ggplot(data = d,
            aes(x = Language,
                y = Entropy,
                fill = factor(Corpus)))
p + geom_bar(stat = "identity",
             position = position_dodge(0.9)) +
    geom_errorbar(limits,
                  position = position_dodge(0.9),
                  width = .25) +
    labs(x = "Language", y = "Entropy") +
    ggtitle("") +
    scale_fill_discrete(name = "Corpus") +
    facet_grid(rows = vars(Type)) +
    theme_bw()
dev.off()
