def getMinimumConflicts(primary: str, secondary: str) -> int:
    n, m = len(primary), len(secondary)
    A = 26

    # GP[i][c] = count of chars in primary[0:i] with value > c
    GP = [[0] * A for _ in range(n + 1)]
    for i in range(1, n + 1):
        x = ord(primary[i - 1]) - ord('a')
        for c in range(A):
            GP[i][c] = GP[i - 1][c] + (1 if c < x else 0)

    GS = [[0] * A for _ in range(m + 1)]
    for j in range(1, m + 1):
        x = ord(secondary[j - 1]) - ord('a')
        for c in range(A):
            GS[j][c] = GS[j - 1][c] + (1 if c < x else 0)

    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        x = ord(primary[i - 1]) - ord('a')
        dp[i][0] = dp[i - 1][0] + GP[i - 1][x] + GS[0][x]

    for j in range(1, m + 1):
        y = ord(secondary[j - 1]) - ord('a')
        dp[0][j] = dp[0][j - 1] + GP[0][y] + GS[j - 1][y]

    for i in range(1, n + 1):
        x = ord(primary[i - 1]) - ord('a')
        for j in range(1, m + 1):
            y = ord(secondary[j - 1]) - ord('a')
            cost_p = GP[i - 1][x] + GS[j][x]
            cost_s = GP[i][y] + GS[j - 1][y]
            dp[i][j] = min(dp[i - 1][j] + cost_p, dp[i][j - 1] + cost_s)

    return dp[n][m]



ans = getMinimumConflicts('dae', 'add')
print(ans)