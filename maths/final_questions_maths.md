### Question ID: 6293d2e5d2fa4e198bce9aaaf7a87f2d
**Question:** Consider an infinite discrete system of masses $u_i$, $i \in \mathbb{Z}$, connected by springs. The displacement of the $i$-th mass from its equilibrium position is given by $u_i$. The restoring force on the $i$-th mass depends nonlocally on the displacements of all other masses according to the difference equation

 $$-\Delta u_i = \sum_{j=-\infty}^{\infty} J_{ij}(u_i - u_j) = f_i,$$

 where $\Delta u_i = u_{i+1} - 2u_i + u_{i-1}$, $f_i$ is an external force applied to the $i$-th mass, and $J_{ij} = J_{ji} > 0$ represents the coupling strength between masses $i$ and $j$, with $J_{ii} = 0$.  Assume the $J_{ij}$ decay rapidly as $|i-j|$ increases, specifically, $J_{ij} = \frac{1}{(1 + (i-j)^2)^2}$.  Suppose $f_i = \delta_{i,0}$, where $\delta_{i,0}$ is the Kronecker delta. Find the value of $u_0$ in terms of a converging infinite sum, assuming the solution $u_i$ is unique and exists in a suitable Hilbert space.
### Question ID: b43c6fbcca9844b8bc393f21d74fdb11
**Question:** Let $H$ be a real Hilbert space, and let $B \subset H$ be a closed ball of radius $R > 0$ centered at the origin. Define a functional $F: B \to \mathbb{R}$ by

 $$F(u) = \frac{1}{2}\sum_{i=1}^{N} a_i \|u - v_i\|^2,$$

 where $a_i > 0$ are constants, and $v_i \in H$ are fixed vectors with $\|v_i\| > R$ for all $i=1,\ldots, N$. Assume that $\sum_{i=1}^{N} a_i = 1$. Determine the minimum value of $F(u)$ on $B$. Express your answer in terms of $a_i, v_i$ and $R$.
### Question ID: 905dc5108725406bb8b27808791f8b56
**Question:** Consider the discrete eigenvalue problem for a function $u_i$ defined on the integers $i \in \{1, 2, \ldots, N\}$. The eigenvalue problem is given by:

 $$-\Delta u_i = \lambda u_i, \quad i \in \{1, 2, \ldots, N\},$$

 where $\Delta u_i = u_{i+1} - 2u_i + u_{i-1}$ with boundary conditions $u_0 = u_{N+1} = 0$. *Furthermore*, we require that the eigenfunction also satisfies the constraint $\sum_{i=1}^N u_i = 0$. Assuming such a solution exists for some $\lambda > 0$, find the smallest eigenvalue $\lambda_1 > 0$ that satisfies both the equation and this constraint. Express $\lambda_1$ as a closed form expression involving trigonometric functions and $N$.
### Question ID: 5e23492901a64c6aaf4ed73dc535b294
**Question:** Consider the sequence $u_n$ defined by the recurrence relation

 $$u_{n+1} = a u_n + b u_{n-1}, \quad n \ge 1,$$

 with initial conditions $u_0 = 2$ and $u_1 = a+1$, where $a$ and $b$ are real numbers such that $a^2 + 4b > 0$ and $b \ne 0$. Now, let $v_n = u_n + c \cdot n$, where $c$ is a constant. Find the generating function $V(z) = \sum_{n=0}^\infty v_n z^n$ in closed form. Express your answer in terms of $a, b, c$ and $z$.
### Question ID: cbab6fa56ada4f49832eb332b8b3bc64
**Question:** Consider the nonlocal discrete problem:

  $$-u_{i+1} + 2u_i - u_{i-1} = f_i + \alpha \sum_{j=1}^N u_j, \quad i = 1, 2, \dots, N,$$

  with boundary conditions $u_0 = u_{N+1} = 0$, where $f_i$ are given values, and $\alpha$ is a constant. Find the value of $\sum_{j=1}^N u_j$ in terms of $f_i$, $N$, and $\alpha$. Assume that $2N+1+\alpha N(N+1) \neq 0$.
### Question ID: 0b8f90884f2f4de99855e302e4de7b75
**Question:** A uniform, solid sphere of mass $M$ and radius $R$ is released from rest on an inclined plane that makes an angle $\theta$ with the horizontal. The coefficient of static friction between the sphere and the plane is $\mu_s$. What is the maximum value of $\theta$ for which the sphere will roll without slipping? Express your answer in terms of $\mu_s$.
### Question ID: e15f97b755614d6aa11c1b4fa436a5e9
**Question:** A particle of mass $m$ is confined to move in a one-dimensional potential $V(x) = \frac{1}{2} k x^2 + \frac{\lambda}{4} x^4$, where $k > 0$ and $\lambda > 0$. Use perturbation theory to calculate the first-order correction to the energy levels of the harmonic oscillator. Express your answer in terms of $m$, $k$, $\lambda$, and the quantum number $n$. You may find the following integral helpful: $\int_{-\infty}^{\infty} x^4 e^{-ax^2} dx = \frac{3}{4a^2}\sqrt{\frac{\pi}{a}}$.
### Question ID: 1098132977b244329574d929f663c470
**Question:** Two identical conducting spheres, each of radius $a$, are separated by a large distance $d$ ($d \gg a$). One sphere has a charge $+Q$, and the other has a charge $-Q$. Find an approximate expression for the electrostatic potential midway between the two spheres, relative to infinity. Give your answer to order $(a/d)^3$.
### Question ID: a60f7cb9d8404f9cbf61a80cbb937f3f
**Question:** A relativistic rocket starts from rest and accelerates with a constant proper acceleration $a$. Determine the rocket's velocity $v(t)$ and position $x(t)$ as a function of the time $t$ measured by an observer in the initial rest frame. Assume the rocket starts at $x(0) = 0$.
### Question ID: ba754c265f774c0fa563a445206ef9d1
**Question:** Consider a gas of $N$ identical, non-interacting particles of mass $m$ in a three-dimensional box of volume $V$ at temperature $T$. Assuming the particles are indistinguishable and obey Maxwell-Boltzmann statistics, calculate the probability that all $N$ particles are located in one half of the box. Express your answer in terms of $N$.
