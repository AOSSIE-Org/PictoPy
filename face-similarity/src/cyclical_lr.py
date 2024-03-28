def cyclical_learning_rate(base_lr, max_lr, max_mom, base_mom, stepsize, decrease_base_by=0.15):

    while True:
        learning_rate_factor = (max_lr - base_lr) / stepsize
        momentum_factor = (max_mom - base_mom) / stepsize

        if base_mom > max_mom:
            print("Error, base momentum has to be greater than max momentum.")

        # half cycle
        current_lr = base_lr
        current_mom = max_mom
        for i in range(stepsize):
            current_lr += learning_rate_factor
            current_mom -= momentum_factor
            yield current_lr, current_mom

        for i in range(stepsize):
            current_lr -= learning_rate_factor
            current_mom += momentum_factor
            yield current_lr, current_mom


        # reduce learning rate by [decrease_base_by]% in half of a stepsize
        half_stepsize = stepsize // 2
        new_base_lr = base_lr - decrease_base_by * base_lr
        decrease_factor = (base_lr - new_base_lr) / half_stepsize
        for i in range(half_stepsize):
            current_lr -= decrease_factor
            yield current_lr, current_mom

        base_lr = new_base_lr
