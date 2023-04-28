import numpy as np


class GEPSolver:
    def __init__(self, learning_rate=1., epochs=50000, components=1, method="eg", return_eigvals=True, line_search=False, momentum=0.):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.components = components
        self.method = method
        self.rho = 1e-1
        self.BU = None
        self.return_eigvals = return_eigvals
        self.line_search = line_search
        self.momentum = momentum

    def fit(self, A, B):
        u = np.random.rand(A.shape[1], self.components)
        u /= np.sqrt(np.diag(u.T @ B @ u))
        self.velocity = np.zeros_like(u)
        self.track=[]
        for _ in range(self.epochs):
            u += self.momentum * self.velocity
            grads = self.grads(A, B, u)
            if self.line_search:
                self.backtracking_line_search(A, B, u, grads)
            self.velocity = self.momentum * self.velocity - self.learning_rate * grads
            u += self.velocity
            self.track.append(self.objective(A, B, u))
        if self.return_eigvals:
            return u, np.diag(u.T @ A @ u) / np.diag(u.T @ B @ u)
        else:
            return u

    def grads(self, A, B, u):
        Aw = A @ u
        Bw = B @ u
        wAw = u.T @ Aw
        wBw = u.T @ Bw
        if self.method == "delta":
            grads = 2 * Aw - (Aw @ np.triu(wBw) + Bw @ np.triu(wAw))
        elif self.method == "gha":
            grads = 2 * Aw - 2 * Bw @ np.triu(wAw)
        elif self.method == "gamma":
            u /= np.linalg.norm(u, axis=0)
            grads = self.gamma_grads(A, B, u)
        else:
            raise ValueError("Invalid method")
        return -grads

    def objective(self, A, B, u):
        Aw = A @ u
        Bw = B @ u
        wAw = u.T @ Aw
        wBw = u.T @ Bw
        if self.method == "delta":
            return -2*np.trace(wAw) + np.diag(wAw)@np.diag(wBw) + 2 * np.triu(wAw*wBw,1).sum()
        elif self.method == "gha":
            return -2*np.trace(wAw) + np.diag(wAw)@np.diag(wBw) + 2 * np.triu(wAw*wBw,1).sum()
        elif self.method == "gamma":
            return -np.diag(wAw) / np.diag(wBw)
        else:
            raise ValueError("Invalid method")

    def backtracking_line_search(self, A, B, u, grads):
        while self.objective(A, B, u - self.learning_rate * grads) > self.objective(A, B, u) - self.rho * self.learning_rate * np.linalg.norm(grads) ** 2:
            self.learning_rate*=0.9
        return

    def gamma_grads(self, A, B, u):
        Aw = A @ u
        Bw = B @ u
        wAw = u.T @ Aw
        wBw = u.T @ Bw
        check = np.diag(wAw) / np.diag(wBw)
        y = u / np.sqrt(np.diag(wBw))
        rewards = Aw * np.diag(wBw) - Bw * np.diag(wAw)
        Ay = A @ y
        By = B @ y
        penalties = By @ np.triu(Ay.T @ u * np.diag(wBw), 1) - Bw * np.diag(np.tril(u.T @ By, -1) @ Ay.T @ u)
        grads = rewards - penalties
        return grads


def main():
    p=30
    # A random generalized eigenvalue problem with symetric matrices A and B where A is not positive definite
    A = np.random.rand(p,p)
    B = np.random.rand(p,p)
    A = A.T @ A
    U, S, Vt = np.linalg.svd(A)
    # make S decay linearly
    S = np.linspace(10, 1, p)
    A = U @ np.diag(S) @ Vt
    B = B.T @ B

    from scipy.linalg import eigh
    # get largest eigenvalue and eigenvector
    w, u_ = eigh(A, B)
    v_true=np.diag(u_.T @ A @ u_)
    delta_ls = GEPSolver(components=10, method="delta", line_search=True)
    u_d_ls, v_d_ls = delta_ls.fit(A, B)
    delta = GEPSolver(components=10, method="delta", learning_rate=1e-5)
    u_d, v_d = delta.fit(A, B)
    delta_n = GEPSolver(components=10, method="delta", learning_rate=1e-5, momentum=0.9)
    u_d_n, v_d_n = delta_n.fit(A, B)

    #plot the objective
    import matplotlib.pyplot as plt
    plt.plot(delta_ls.track, label="line search")
    plt.plot(delta.track, label="gradient descent")
    plt.plot(delta_n.track, label="momentum")
    plt.xlabel("iterations")
    plt.ylabel("objective")
    plt.legend()
    plt.show()



if __name__ == '__main__':
    main()
