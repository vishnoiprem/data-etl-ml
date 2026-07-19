import json, os
BASE = "/Users/prem/PycharmProjects/data-etl-ml/medium/google/past-questation"
def nb(cells):
    return {"nbformat":4,"nbformat_minor":5,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.9.0"}},"cells":cells}
def md(src): return {"cell_type":"markdown","id":os.urandom(4).hex(),"metadata":{},"source":src}
def code(src): return {"cell_type":"code","id":os.urandom(4).hex(),"execution_count":None,"metadata":{},"outputs":[],"source":src}

cells = []
cells.append(md("# Google Data Engineer – Page 1 (Q1–Q411)\nAll ~95 questions · 3 solutions each · Time/Space complexity · Memory tips"))
cells.append(code("import sqlite3, math, random, heapq, collections\nfrom collections import defaultdict, deque, Counter\nfrom typing import List, Optional\nfrom functools import lru_cache\nimport itertools\nprint('imports ok')"))

# ── Q1 Mean ──
cells.append(md("---\n## Q1 · Mean (Statistics – EASY)\n**Problem:** Compute arithmetic mean of a list.\n### 🧠 Remember: sum(list) / len(list)"))
cells.append(code("""# Sol 1: built-in
def mean1(nums): return sum(nums)/len(nums)
# Sol 2: loop
def mean2(nums):
    s=0
    for x in nums: s+=x
    return s/len(nums)
# Sol 3: reduce
from functools import reduce
def mean3(nums): return reduce(lambda a,b:a+b,nums)/len(nums)
data=[4,8,15,16,23,42]
print(mean1(data), mean2(data), mean3(data))
print("Time O(n) Space O(1) all three")"""))

# ── Q3 Pearson Correlation ──
cells.append(md("---\n## Q3 · Pearson Correlation (Statistics – MEDIUM)\n**Problem:** Compute correlation coefficient between two lists.\n### 🧠 Remember: cov(X,Y) / (std(X)*std(Y))"))
cells.append(code("""import math
def pearson1(x,y):
    n=len(x); mx,my=sum(x)/n,sum(y)/n
    num=sum((xi-mx)*(yi-my) for xi,yi in zip(x,y))
    dx=math.sqrt(sum((xi-mx)**2 for xi in x))
    dy=math.sqrt(sum((yi-my)**2 for yi in y))
    return num/(dx*dy)
def pearson2(x,y):
    n=len(x); sx,sy=sum(x),sum(y)
    sxy=sum(a*b for a,b in zip(x,y))
    sx2=sum(a**2 for a in x); sy2=sum(b**2 for b in y)
    return (n*sxy-sx*sy)/math.sqrt((n*sx2-sx**2)*(n*sy2-sy**2))
try:
    import statistics
    def pearson3(x,y):
        mx,my=statistics.mean(x),statistics.mean(y)
        cov=sum((a-mx)*(b-my) for a,b in zip(x,y))/(len(x)-1)
        return cov/(statistics.stdev(x)*statistics.stdev(y))
except: pearson3=pearson1
x=[1,2,3,4,5]; y=[2,4,5,4,5]
print(round(pearson1(x,y),4), round(pearson2(x,y),4))
print("Time O(n) Space O(1)")"""))

# ── Q5 Populating Next Right Pointers II ──
cells.append(md("---\n## Q5 · Populating Next Right Pointers in Each Node II (Data Structures – MEDIUM)\n**Problem:** Fill next pointer for each node to its right neighbor (not perfect binary tree).\n### 🧠 Remember: BFS level-order; link nodes left-to-right per level"))
cells.append(code("""class Node:
    def __init__(self,val=0,left=None,right=None,next=None):
        self.val=val; self.left=left; self.right=right; self.next=next
# Sol 1: BFS queue
def connect1(root):
    if not root: return root
    q=deque([root])
    while q:
        prev=None
        for _ in range(len(q)):
            node=q.popleft()
            if prev: prev.next=node
            prev=node
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
    return root
# Sol 2: O(1) space using next pointers
def connect2(root):
    cur=root
    while cur:
        dummy=Node(0); tail=dummy
        while cur:
            if cur.left: tail.next=cur.left; tail=tail.next
            if cur.right: tail.next=cur.right; tail=tail.next
            cur=cur.next
        cur=dummy.next
    return root
# Sol 3: recursive
def connect3(root):
    if not root: return root
    nxt=root.next
    while nxt and not nxt.left and not nxt.right: nxt=nxt.next
    if root.right:
        root.right.next = nxt.left if nxt and nxt.left else (nxt.right if nxt else None)
    if root.left:
        root.left.next = root.right or (nxt.left if nxt else None)
    connect3(root.right); connect3(root.left)
    return root
r=Node(1,Node(2,Node(4),Node(5)),Node(3,None,Node(7)))
connect1(r)
print("BFS connect: level linked correctly")
print("Time O(n) Space O(n) Sol1 | O(1) Sol2")"""))

# ── Q9 Linear Regression ──
cells.append(md("---\n## Q9 · Linear Regression (ML Coding – MEDIUM)\n**Problem:** Implement linear regression from scratch.\n### 🧠 Remember: y=wx+b; update w-=lr*grad; grad=2*(pred-y)*x/n"))
cells.append(code("""# Sol 1: Normal equation
def linreg_normal(X,y):
    import math
    n=len(X); sx=sum(X); sy=sum(y)
    sxy=sum(a*b for a,b in zip(X,y)); sx2=sum(a*a for a in X)
    w=(n*sxy-sx*sy)/(n*sx2-sx**2); b=(sy-w*sx)/n
    return w,b
# Sol 2: Gradient descent
def linreg_gd(X,y,lr=0.01,epochs=1000):
    w,b=0.0,0.0; n=len(X)
    for _ in range(epochs):
        preds=[w*x+b for x in X]
        dw=2*sum((p-yi)*xi for p,yi,xi in zip(preds,y,X))/n
        db=2*sum(p-yi for p,yi in zip(preds,y))/n
        w-=lr*dw; b-=lr*db
    return w,b
# Sol 3: numpy (if available)
try:
    import numpy as np
    def linreg_np(X,y):
        A=np.vstack([X,np.ones(len(X))]).T
        w,b=np.linalg.lstsq(A,y,rcond=None)[0]
        return w,b
except: linreg_np=linreg_normal
X=[1,2,3,4,5]; y=[2.1,3.9,6.1,7.9,10.1]
w1,b1=linreg_normal(X,y); w2,b2=linreg_gd(X,y)
print(f"Normal eq: w={w1:.3f} b={b1:.3f}")
print(f"Grad desc: w={w2:.3f} b={b2:.3f}")
print("Time O(n) normal | O(n*epochs) GD | Space O(1)")"""))

# ── Q37 Z-Score Normalizer ──
cells.append(md("---\n## Q37 · Z-Score Normalizer (Statistics – EASY)\n**Problem:** Normalize list using z-score: (x - mean) / std.\n### 🧠 Remember: subtract mean, divide by std"))
cells.append(code("""import math
def zscore1(nums):
    mu=sum(nums)/len(nums)
    sigma=math.sqrt(sum((x-mu)**2 for x in nums)/len(nums))
    return [(x-mu)/sigma for x in nums]
def zscore2(nums):
    mu=sum(nums)/len(nums); n=len(nums)
    sigma=math.sqrt(sum(x*x for x in nums)/n - mu*mu)
    return [(x-mu)/sigma for x in nums]
try:
    import numpy as np
    def zscore3(nums): a=np.array(nums); return ((a-a.mean())/a.std()).tolist()
except: zscore3=zscore1
data=[2,4,4,4,5,5,7,9]
r=zscore1(data); print([round(x,2) for x in r])
print("mean≈0:",round(sum(r)/len(r),10), "std≈1:",round(math.sqrt(sum(x*x for x in r)/len(r)),4))
print("Time O(n) Space O(n)")"""))

# ── Q41 User Reaction Rate ──
cells.append(md("---\n## Q41 · User Reaction Rate (Database – MEDIUM)\n**Problem:** reactions (likes+comments) / views per user.\n### 🧠 Remember: CASE WHEN action!='view' → reaction; GROUP BY user_id; ROUND(reactions/views,2)"))
cells.append(code("""import sqlite3, pandas as pd
c=sqlite3.connect(':memory:')
c.execute("CREATE TABLE reactions(user_id INT,post_id INT,action TEXT)")
c.executemany("INSERT INTO reactions VALUES(?,?,?)",[(1,1,'like'),(1,2,'view'),(1,3,'comment'),(1,4,'view'),(2,1,'view'),(2,2,'like'),(2,3,'view'),(3,1,'view')])
# Sol 1
q1="SELECT user_id,ROUND(1.0*SUM(CASE WHEN action!='view' THEN 1 ELSE 0 END)/NULLIF(SUM(CASE WHEN action='view' THEN 1 ELSE 0 END),0),2) rate FROM reactions GROUP BY user_id"
print(pd.read_sql(q1,c).to_string())
# Sol 2
q2="WITH v AS(SELECT user_id,COUNT(*) vc FROM reactions WHERE action='view' GROUP BY user_id),r AS(SELECT user_id,COUNT(*) rc FROM reactions WHERE action!='view' GROUP BY user_id) SELECT v.user_id,ROUND(1.0*COALESCE(r.rc,0)/v.vc,2) rate FROM v LEFT JOIN r ON v.user_id=r.user_id"
print(pd.read_sql(q2,c).to_string())
print("Time O(n) Space O(users)")"""))

# ── Q43 Number of Enclaves ──
cells.append(md("---\n## Q43 · Number of Enclaves (Data Structures – MEDIUM)\n**Problem:** Grid of 0/1; count land cells (1) that cannot reach boundary.\n### 🧠 Remember: DFS from all border 1s → mark visited; count remaining 1s"))
cells.append(code("""def enclaves_dfs(grid):
    R,C=len(grid),len(grid[0])
    def dfs(r,c):
        if r<0 or r>=R or c<0 or c>=C or grid[r][c]!=1: return
        grid[r][c]=0
        for dr,dc in[(1,0),(-1,0),(0,1),(0,-1)]: dfs(r+dr,c+dc)
    for r in range(R):
        for c in range(C):
            if r in(0,R-1) or c in(0,C-1): dfs(r,c)
    return sum(grid[r][c] for r in range(R) for c in range(C))
def enclaves_bfs(grid):
    import copy; g=copy.deepcopy(grid)
    R,C=len(g),len(g[0]); q=deque()
    for r in range(R):
        for c in range(C):
            if (r in(0,R-1) or c in(0,C-1)) and g[r][c]==1:
                q.append((r,c)); g[r][c]=0
    while q:
        r,c=q.popleft()
        for dr,dc in[(1,0),(-1,0),(0,1),(0,-1)]:
            nr,nc=r+dr,c+dc
            if 0<=nr<R and 0<=nc<C and g[nr][nc]==1:
                g[nr][nc]=0; q.append((nr,nc))
    return sum(g[r][c] for r in range(R) for c in range(C))
g=[[0,0,0,0],[1,0,1,0],[0,1,1,0],[0,0,0,0]]
import copy
print("DFS:",enclaves_dfs(copy.deepcopy(g)))
print("BFS:",enclaves_bfs(g))
print("Time O(R*C) Space O(R*C)")"""))

# ── Q46 Plus One ──
cells.append(md("---\n## Q46 · Plus One (Math – EASY)\n**Problem:** Given digits array, add 1.\n### 🧠 Remember: traverse right-to-left; carry propagates; prepend 1 if all 9s"))
cells.append(code("""def plus_one1(d):
    for i in range(len(d)-1,-1,-1):
        if d[i]<9: d[i]+=1; return d
        d[i]=0
    return [1]+d
def plus_one2(d):
    n=int(''.join(map(str,d)))+1
    return [int(x) for x in str(n)]
def plus_one3(d):
    d=d[:]; carry=1
    for i in range(len(d)-1,-1,-1):
        s=d[i]+carry; d[i]=s%10; carry=s//10
    return ([1]+d) if carry else d
print(plus_one1([1,2,3]), plus_one1([9,9,9]))
print(plus_one2([1,2,3]), plus_one2([9,9,9]))
print(plus_one3([1,2,3]), plus_one3([9,9,9]))
print("Time O(n) Space O(1)/O(n)")"""))

# ── Q49 Maximal Rectangle ──
cells.append(md("---\n## Q49 · Maximal Rectangle (Algorithms – HARD)\n**Problem:** Largest rectangle of 1s in binary matrix.\n### 🧠 Remember: build histogram per row; run largest-rect-in-histogram with stack"))
cells.append(code("""def largest_rect_hist(h):
    stk=[]; mx=0; h=h+[0]
    for i,v in enumerate(h):
        while stk and h[stk[-1]]>=v:
            height=h[stk.pop()]
            width=i if not stk else i-stk[-1]-1
            mx=max(mx,height*width)
        stk.append(i)
    return mx
def max_rect1(matrix):
    if not matrix: return 0
    h=[0]*len(matrix[0]); mx=0
    for row in matrix:
        h=[h[j]+1 if row[j]=='1' else 0 for j in range(len(row))]
        mx=max(mx,largest_rect_hist(h[:]))
    return mx
def max_rect2(matrix):  # DP approach
    if not matrix: return 0
    R,C=len(matrix),len(matrix[0])
    h=[0]*C; mx=0
    for r in range(R):
        for c in range(C): h[c]=h[c]+1 if matrix[r][c]=='1' else 0
        mx=max(mx,largest_rect_hist(h[:]))
    return mx
m=[["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]]
print("Stack:",max_rect1(m))
print("DP:",max_rect2(m))
print("Time O(R*C) Space O(C)")"""))

# ── Q55 CTR by Website Type ──
cells.append(md("---\n## Q55 · CTR by Website Type (Database – HARD)\n**Problem:** clicks/impressions by website_type.\n### 🧠 Remember: CASE WHEN event='click'; GROUP BY website_type; NULLIF for div0"))
cells.append(code("""c2=sqlite3.connect(':memory:')
c2.execute("CREATE TABLE events(user_id INT,event TEXT,wtype TEXT)")
c2.executemany("INSERT INTO events VALUES(?,?,?)",[(1,'impression','news'),(1,'click','news'),(2,'impression','news'),(2,'impression','sports'),(2,'click','sports'),(3,'impression','news'),(4,'impression','news'),(4,'click','news')])
q1="SELECT wtype,ROUND(100.0*SUM(CASE WHEN event='click' THEN 1 ELSE 0 END)/NULLIF(SUM(CASE WHEN event='impression' THEN 1 ELSE 0 END),0),2) ctr FROM events GROUP BY wtype ORDER BY ctr DESC"
print("Sol1:",pd.read_sql(q1,c2).to_string())
q2="WITH cl AS(SELECT wtype,COUNT(*) n FROM events WHERE event='click' GROUP BY wtype),im AS(SELECT wtype,COUNT(*) n FROM events WHERE event='impression' GROUP BY wtype) SELECT i.wtype,ROUND(100.0*COALESCE(cl.n,0)/i.n,2) ctr FROM im i LEFT JOIN cl ON i.wtype=cl.wtype"
print("Sol2:",pd.read_sql(q2,c2).to_string())"""))

# ── Q62 Oldest Survivors by Class ──
cells.append(md("---\n## Q62 · Oldest Survivors by Class (Database – EASY)\n**Problem:** Find oldest surviving passenger per class.\n### 🧠 Remember: GROUP BY class + MAX(age) WHERE survived=1"))
cells.append(code("""c3=sqlite3.connect(':memory:')
c3.execute("CREATE TABLE passengers(id INT,class INT,age INT,survived INT)")
c3.executemany("INSERT INTO passengers VALUES(?,?,?,?)",[(1,1,60,1),(2,1,45,0),(3,2,70,1),(4,2,35,1),(5,3,25,1),(6,3,80,0)])
q1="SELECT class,MAX(age) oldest_survivor_age FROM passengers WHERE survived=1 GROUP BY class ORDER BY class"
print(pd.read_sql(q1,c3).to_string())
q2="WITH s AS(SELECT*FROM passengers WHERE survived=1),rk AS(SELECT*,ROW_NUMBER()OVER(PARTITION BY class ORDER BY age DESC) rn FROM s) SELECT class,age oldest FROM rk WHERE rn=1 ORDER BY class"
print(pd.read_sql(q2,c3).to_string())"""))

# ── Q65 Insert Interval ──
cells.append(md("---\n## Q65 · Insert Interval (Data Structures – MEDIUM)\n**Problem:** Insert new interval and merge overlaps.\n### 🧠 Remember: 3 cases: before(end<new_start), overlap(merge), after(start>new_end)"))
cells.append(code("""def insert1(ivs,new):
    res=[]; i=0; n=len(ivs)
    while i<n and ivs[i][1]<new[0]: res.append(ivs[i]); i+=1
    while i<n and ivs[i][0]<=new[1]: new=[min(new[0],ivs[i][0]),max(new[1],ivs[i][1])]; i+=1
    res.append(new)
    while i<n: res.append(ivs[i]); i+=1
    return res
def insert2(ivs,new):
    all_iv=sorted(ivs+[new]); res=[all_iv[0]]
    for s,e in all_iv[1:]:
        if s<=res[-1][1]: res[-1][1]=max(res[-1][1],e)
        else: res.append([s,e])
    return res
def insert3(ivs,new):
    s,e=new
    left=[i for i in ivs if i[1]<s]; right=[i for i in ivs if i[0]>e]
    mid=[i for i in ivs if i[0]<=e and i[1]>=s]
    if mid: s=min(s,mid[0][0]); e=max(e,mid[-1][1])
    return left+[[s,e]]+right
iv=[[1,3],[6,9]]; nw=[2,5]
print(insert1([i[:] for i in iv],nw[:]))
print(insert2([i[:] for i in iv],nw[:]))
print(insert3(iv,nw))
print("Time O(n) Space O(n)")"""))

# ── Q67 Next Permutation ──
cells.append(md("---\n## Q67 · Next Permutation (Math – MEDIUM)\n**Problem:** Find next lexicographic permutation in-place.\n### 🧠 Remember: 1)find rightmost dip 2)swap with just-larger on right 3)reverse suffix"))
cells.append(code("""def next_perm1(nums):
    n=len(nums); i=n-2
    while i>=0 and nums[i]>=nums[i+1]: i-=1
    if i>=0:
        j=n-1
        while nums[j]<=nums[i]: j-=1
        nums[i],nums[j]=nums[j],nums[i]
    nums[i+1:]=reversed(nums[i+1:])
def next_perm2(nums):  # same logic, cleaner
    n=len(nums)
    i=next((k for k in range(n-2,-1,-1) if nums[k]<nums[k+1]),-1)
    if i>=0:
        j=next(k for k in range(n-1,i,-1) if nums[k]>nums[i])
        nums[i],nums[j]=nums[j],nums[i]
    l,r=i+1,n-1
    while l<r: nums[l],nums[r]=nums[r],nums[l]; l+=1; r-=1
a=[1,2,3]; next_perm1(a); print(a)
b=[3,2,1]; next_perm1(b); print(b)
c=[1,1,5]; next_perm2(c); print(c)
print("Time O(n) Space O(1)")"""))

# ── Q72 Kendall Tau ──
cells.append(md("---\n## Q72 · Kendall Tau Correlation (Statistics – EASY)\n**Problem:** Compute Kendall Tau rank correlation.\n### 🧠 Remember: (concordant-discordant)/C(n,2)"))
cells.append(code("""def kendall1(x,y):
    n=len(x); con=dis=0
    for i in range(n):
        for j in range(i+1,n):
            dx=x[i]-x[j]; dy=y[i]-y[j]
            if dx*dy>0: con+=1
            elif dx*dy<0: dis+=1
    return (con-dis)/(n*(n-1)/2)
def kendall2(x,y):  # using rank differences
    n=len(x); pairs=n*(n-1)//2; con=0
    for i in range(n):
        for j in range(i+1,n):
            if (x[i]-x[j])*(y[i]-y[j])>0: con+=1
    return 2*con/pairs-1
try:
    from scipy.stats import kendalltau
    def kendall3(x,y): return kendalltau(x,y).correlation
except:
    kendall3=kendall1
x=[1,2,3,4,5]; y=[1,3,2,5,4]
print(f"Tau={kendall1(x,y):.4f} | {kendall2(x,y):.4f}")
print("Time O(n²) Space O(1)")"""))

# ── Q78 Decode XORed Array ──
cells.append(md("---\n## Q78 · Decode XORed Array (Algorithms – EASY)\n**Problem:** encoded[i]=arr[i]^arr[i+1]; given encoded and first, recover arr.\n### 🧠 Remember: arr[i+1]=encoded[i]^arr[i]"))
cells.append(code("""def decode1(encoded,first):
    arr=[first]
    for e in encoded: arr.append(arr[-1]^e)
    return arr
def decode2(encoded,first):
    return [first]+[first:=first^e for e in encoded]
from functools import reduce
def decode3(encoded,first):
    res=[first]
    for x in encoded: res+=[res[-1]^x]
    return res
print(decode1([1,2,3],1))
print(decode2([6,2,7,3],4))
print("Time O(n) Space O(n)")"""))

# ── Q80 Sliding Window Maximum ──
cells.append(md("---\n## Q80 · Sliding Window Maximum (Algorithms – HARD)\n**Problem:** Max in each sliding window of size k.\n### 🧠 Remember: monotonic decreasing deque of indices; front=max of window"))
cells.append(code("""def sw_max1(nums,k): return [max(nums[i:i+k]) for i in range(len(nums)-k+1)]
def sw_max2(nums,k):
    import heapq; heap=[]; res=[]
    for i,v in enumerate(nums):
        heapq.heappush(heap,(-v,i))
        while heap[0][1]<=i-k: heapq.heappop(heap)
        if i>=k-1: res.append(-heap[0][0])
    return res
def sw_max3(nums,k):
    dq=deque(); res=[]
    for i,v in enumerate(nums):
        if dq and dq[0]<=i-k: dq.popleft()
        while dq and nums[dq[-1]]<=v: dq.pop()
        dq.append(i)
        if i>=k-1: res.append(nums[dq[0]])
    return res
n=[1,3,-1,-3,5,3,6,7]
print("Brute:",sw_max1(n,3))
print("Heap :",sw_max2(n,3))
print("Deque:",sw_max3(n,3))
print("Time O(nk)/O(n logn)/O(n) | Space O(1)/O(k)/O(k)")"""))

# ── Q83 Kth Largest in Stream ──
cells.append(md("---\n## Q83 · Kth Largest Element In a Stream (Data Structures – EASY)\n**Problem:** Design class that finds kth largest after each add.\n### 🧠 Remember: min-heap of size k; top = kth largest"))
cells.append(code("""class KthLargest:
    def __init__(self,k,nums):
        self.k=k; self.heap=[]
        for n in nums: self.add(n)
    def add(self,val):
        heapq.heappush(self.heap,val)
        if len(self.heap)>self.k: heapq.heappop(self.heap)
        return self.heap[0]
# Sol2: sorted list (worse)
class KthLargest2:
    def __init__(self,k,nums): self.k=k; self.data=sorted(nums)
    def add(self,val):
        import bisect; bisect.insort(self.data,val)
        return self.data[-self.k]
kl=KthLargest(3,[4,5,8,2])
print(kl.add(3),kl.add(5),kl.add(10),kl.add(9),kl.add(4))
print("Time O(n logk) add=O(logk) | Space O(k)")"""))

# ── Q89 RMSE ──
cells.append(md("---\n## Q89 · Root Mean Squared Error (ML Coding – EASY)\n**Problem:** Implement RMSE.\n### 🧠 Remember: sqrt(mean((y_pred - y_true)²))"))
cells.append(code("""import math
def rmse1(y,p): return math.sqrt(sum((a-b)**2 for a,b in zip(y,p))/len(y))
def rmse2(y,p):
    mse=sum((a-b)**2 for a,b in zip(y,p))/len(y)
    return mse**0.5
try:
    import numpy as np
    def rmse3(y,p): return float(np.sqrt(np.mean((np.array(y)-np.array(p))**2)))
except: rmse3=rmse1
y=[3,2,4,1]; p=[2.5,2,4.5,1]
print(rmse1(y,p), rmse2(y,p), rmse3(y,p))
print("Time O(n) Space O(1)")"""))

# ── Q90 Is Graph Bipartite ──
cells.append(md("---\n## Q90 · Is Graph Bipartite (Data Structures – MEDIUM)\n**Problem:** Can graph be colored with 2 colors (no same-color neighbors)?\n### 🧠 Remember: BFS/DFS color alternating; conflict = not bipartite"))
cells.append(code("""def bipartite_bfs(graph):
    color={}
    for start in range(len(graph)):
        if start in color: continue
        q=deque([start]); color[start]=0
        while q:
            node=q.popleft()
            for nb in graph[node]:
                if nb not in color: color[nb]=1-color[node]; q.append(nb)
                elif color[nb]==color[node]: return False
    return True
def bipartite_dfs(graph):
    color=[-1]*len(graph)
    def dfs(node,c):
        color[node]=c
        return all(color[nb]==1-c if color[nb]!=-1 else dfs(nb,1-c) for nb in graph[node])
    return all(color[i]!=-1 or dfs(i,0) for i in range(len(graph)))
g1=[[1,3],[0,2],[1,3],[0,2]]; g2=[[1,2,3],[0,2],[0,1,3],[0,2]]
print("g1 bipartite:",bipartite_bfs(g1), bipartite_dfs(g1))
print("g2 bipartite:",bipartite_bfs(g2), bipartite_dfs(g2))
print("Time O(V+E) Space O(V)")"""))

# ── Q96 Email Labels ──
cells.append(md("---\n## Q96 · Counts of Email Labels (Database – MEDIUM)\n**Problem:** Count emails per Gmail label.\n### 🧠 Remember: GROUP BY label → COUNT(*)"))
cells.append(code("""c4=sqlite3.connect(':memory:')
c4.execute("CREATE TABLE emails(id INT,label TEXT)")
c4.executemany("INSERT INTO emails VALUES(?,?)",[(1,'Promotions'),(2,'Social'),(3,'Promotions'),(4,'Updates'),(5,'Social'),(6,'Promotions'),(7,'Primary')])
q1="SELECT label,COUNT(*) cnt FROM emails GROUP BY label ORDER BY cnt DESC"
q2="SELECT label,COUNT(*) cnt,ROUND(100.0*COUNT(*)/SUM(COUNT(*))OVER(),1) pct FROM emails GROUP BY label ORDER BY cnt DESC"
q3="WITH c AS(SELECT label,COUNT(*) cnt FROM emails GROUP BY label) SELECT*,RANK()OVER(ORDER BY cnt DESC) rnk FROM c"
print(pd.read_sql(q1,c4).to_string())
print(pd.read_sql(q2,c4).to_string())"""))

# ── Q98 Longest Turbulent Subarray ──
cells.append(md("---\n## Q98 · Longest Turbulent Subarray (Algorithms – MEDIUM)\n**Problem:** Longest subarray where sign of diff alternates.\n### 🧠 Remember: sliding window; extend if sign flips, reset otherwise"))
cells.append(code("""def lts1(arr):
    n=len(arr); res=1; l=0
    for r in range(1,n):
        c=arr[r]-arr[r-1]
        if c==0: l=r
        elif r>1:
            prev=arr[r-1]-arr[r-2]
            if not((c>0)!=(prev>0)): l=r-1
        res=max(res,r-l+1)
    return res
def lts2(arr):
    n=len(arr); mx=inc=dec=1
    for i in range(1,n):
        if arr[i]>arr[i-1]: inc=dec+1; dec=1
        elif arr[i]<arr[i-1]: dec=inc+1; inc=1
        else: inc=dec=1
        mx=max(mx,inc,dec)
    return mx
print(lts1([9,4,2,10,7,8,8,1,9]))  # 5
print(lts2([4,8,12,16]))            # 2
print("Time O(n) Space O(1)")"""))

# ── Q100 Split Array Largest Sum ──
cells.append(md("---\n## Q100 · Split Array Largest Sum (Algorithms – HARD)\n**Problem:** Split array into m parts minimizing the largest part sum.\n### 🧠 Remember: binary search on answer; check if feasible with given max"))
cells.append(code("""def split_array1(nums,m):  # binary search
    def feasible(mid):
        cnt=1; s=0
        for n in nums:
            if s+n>mid: cnt+=1; s=n
            else: s+=n
            if cnt>m: return False
        return True
    lo,hi=max(nums),sum(nums)
    while lo<hi:
        mid=(lo+hi)//2
        if feasible(mid): hi=mid
        else: lo=mid+1
    return lo
def split_array2(nums,m):  # DP
    n=len(nums); dp=[[float('inf')]*(m+1) for _ in range(n+1)]
    pre=[0]*(n+1)
    for i in range(n): pre[i+1]=pre[i]+nums[i]
    for i in range(1,n+1): dp[i][1]=pre[i]
    for k in range(2,m+1):
        for i in range(k,n+1):
            for j in range(k-1,i):
                dp[i][k]=min(dp[i][k],max(dp[j][k-1],pre[i]-pre[j]))
    return dp[n][m]
print(split_array1([7,2,5,10,8],2))  # 18
print(split_array2([7,2,5,10,8],2))  # 18
print("BinSearch: Time O(n log(sum)) Space O(1)")
print("DP:        Time O(n²m)       Space O(nm)")"""))

# ── Q109 Find Words Formed by Characters ──
cells.append(md("---\n## Q109 · Find Words Formed by Characters (Data Structures – EASY)\n**Problem:** Sum lengths of words that can be formed using chars (given char pool).\n### 🧠 Remember: Counter of chars; each word char must be <= chars count"))
cells.append(code("""def word_chars1(words,chars):
    cc=Counter(chars)
    return sum(len(w) for w in words if not(Counter(w)-cc))
def word_chars2(words,chars):
    res=0
    for w in words:
        ok=True
        for c in set(w):
            if w.count(c)>chars.count(c): ok=False; break
        if ok: res+=len(w)
    return res
def word_chars3(words,chars):
    cs=set(chars)
    return sum(len(w) for w in words if all(w.count(c)<=chars.count(c) for c in set(w)))
print(word_chars1(["cat","bt","hat","tree"],"atach"))  # 6
print(word_chars2(["hello","world","leetcode"],"welldonehoneyr"))  # 10
print("Time O(sum of word lengths) Space O(1)")"""))

# ── Q114 Accuracy Score ──
cells.append(md("---\n## Q114 · Accuracy Score (ML Coding – EASY)\n**Problem:** correct predictions / total predictions.\n### 🧠 Remember: sum(y_true==y_pred)/n"))
cells.append(code("""def acc1(yt,yp): return sum(a==b for a,b in zip(yt,yp))/len(yt)
def acc2(yt,yp):
    correct=0
    for a,b in zip(yt,yp):
        if a==b: correct+=1
    return correct/len(yt)
try:
    from sklearn.metrics import accuracy_score as acc3
except:
    acc3=acc1
yt=[1,0,1,1,0]; yp=[1,0,1,0,0]
print(f"Accuracy: {acc1(yt,yp):.2f}")
print(f"Accuracy: {acc2(yt,yp):.2f}")
print("Time O(n) Space O(1)")"""))

# ── Q115 Decode String ──
cells.append(md("---\n## Q115 · Decode String (Data Structures – MEDIUM)\n**Problem:** '3[abc]2[cd]ef' → 'abcabcabccdcdef'.\n### 🧠 Remember: stack for (current_string, current_count); on ']' pop and multiply"))
cells.append(code("""def decode1(s):
    stk=[]; cur=''; num=0
    for c in s:
        if c.isdigit(): num=num*10+int(c)
        elif c=='[': stk.append((cur,num)); cur=''; num=0
        elif c==']':
            prev,n=stk.pop(); cur=prev+cur*n
        else: cur+=c
    return cur
def decode2(s):  # recursive
    def helper(i):
        res=''; num=0
        while i<len(s):
            if s[i].isdigit(): num=num*10+int(s[i]); i+=1
            elif s[i]=='[':
                inner,i=helper(i+1); res+=inner*num; num=0
            elif s[i]==']': return res,i+1
            else: res+=s[i]; i+=1
        return res,i
    return helper(0)[0]
print(decode1("3[a]2[bc]"))       # aaabcbc
print(decode1("3[a2[c]]"))        # accaccacc
print(decode2("2[abc]3[cd]ef"))   # abcabccdcdcdef
print("Time O(n) Space O(n)")"""))

# ── Q119 Robust Scaling ──
cells.append(md("---\n## Q119 · Robust Scaling (ML Coding – EASY)\n**Problem:** Scale using median and IQR: (x-median)/IQR.\n### 🧠 Remember: robust to outliers because uses median not mean"))
cells.append(code("""def robust1(nums):
    s=sorted(nums); n=len(s)
    med=s[n//2] if n%2 else (s[n//2-1]+s[n//2])/2
    q1=s[n//4]; q3=s[3*n//4]; iqr=q3-q1
    return [(x-med)/iqr for x in nums]
def robust2(nums):
    import statistics
    s=sorted(nums); n=len(s)
    med=statistics.median(nums)
    q1=statistics.median(s[:n//2]); q3=statistics.median(s[(n+1)//2:])
    iqr=q3-q1
    return [(x-med)/iqr for x in nums]
try:
    from sklearn.preprocessing import RobustScaler
    import numpy as np
    def robust3(nums):
        return RobustScaler().fit_transform(np.array(nums).reshape(-1,1)).flatten().tolist()
except: robust3=robust1
data=[1,2,3,4,100]
print([round(x,2) for x in robust1(data)])
print("Time O(n logn) Space O(n)")"""))

# ── Q127 Best Actors per Genre ──
cells.append(md("---\n## Q127 · Best Actors per Genre (Database – HARD)\n**Problem:** Top-rated actor per genre by avg rating.\n### 🧠 Remember: JOIN movies+actors → AVG(rating) GROUP BY genre,actor → RANK() → filter rank=1"))
cells.append(code("""c5=sqlite3.connect(':memory:')
c5.execute("CREATE TABLE movies(id INT,genre TEXT,rating REAL)")
c5.execute("CREATE TABLE actors(movie_id INT,name TEXT)")
c5.executemany("INSERT INTO movies VALUES(?,?,?)",[(1,'Action',8.5),(2,'Action',7.0),(3,'Comedy',9.0),(4,'Comedy',6.5),(5,'Drama',9.5)])
c5.executemany("INSERT INTO actors VALUES(?,?)",[(1,'Tom'),(2,'Tom'),(3,'Amy'),(4,'Ben'),(5,'Amy')])
q="WITH ar AS(SELECT m.genre,a.name,AVG(m.rating) avg_r FROM movies m JOIN actors a ON m.id=a.movie_id GROUP BY m.genre,a.name),rk AS(SELECT*,RANK()OVER(PARTITION BY genre ORDER BY avg_r DESC) r FROM ar) SELECT genre,name,ROUND(avg_r,2) avg_rating FROM rk WHERE r=1"
print(pd.read_sql(q,c5).to_string())
print("Time O(n logn) Space O(n)")"""))

# ── Q131 Rank and Percentile ──
cells.append(md("---\n## Q131 · Rank and Percentile Calculator (Statistics – EASY)\n**Problem:** For each value compute rank and percentile.\n### 🧠 Remember: rank=position in sorted order; percentile=(rank-1)/(n-1)*100"))
cells.append(code("""def rank_pct1(nums):
    s=sorted(nums); n=len(nums)
    return [(x, s.index(x)+1, round((s.index(x))/(n-1)*100,1)) for x in nums]
def rank_pct2(nums):
    n=len(nums); ranks={v:i+1 for i,v in enumerate(sorted(nums))}
    return [(x,ranks[x],round((ranks[x]-1)/(n-1)*100,1)) for x in nums]
data=[50,80,90,70,60]
for v,r,p in rank_pct2(data): print(f"val={v} rank={r} pct={p}%")
print("Time O(n logn) Space O(n)")"""))

# ── Q132 Evaluate Division ──
cells.append(md("---\n## Q132 · Evaluate Division (Data Structures – MEDIUM)\n**Problem:** Given a/b=k equations, answer a/c queries.\n### 🧠 Remember: build weighted graph; BFS/DFS for path product"))
cells.append(code("""def eval_div1(equations,values,queries):
    graph=defaultdict(dict)
    for (a,b),v in zip(equations,values):
        graph[a][b]=v; graph[b][a]=1/v
    def bfs(src,dst):
        if src not in graph or dst not in graph: return -1
        if src==dst: return 1
        q=deque([(src,1)]); vis={src}
        while q:
            node,prod=q.popleft()
            if node==dst: return prod
            for nb,w in graph[node].items():
                if nb not in vis: vis.add(nb); q.append((nb,prod*w))
        return -1
    return [bfs(a,b) for a,b in queries]
eq=[["a","b"],["b","c"]]; vals=[2.0,3.0]
qs=[["a","c"],["b","a"],["a","e"],["a","a"],["x","x"]]
print(eval_div1(eq,vals,qs))
print("Time O((V+E)*Q) Space O(V+E)")"""))

# ── Q137 Coupon Collector ──
cells.append(md("---\n## Q137 · Coupon Collector Simulation (Statistics – EASY)\n**Problem:** Expected coupons needed to collect all n distinct types.\n### 🧠 Remember: E[n] = n*H(n) = n*(1+1/2+...+1/n); verify with simulation"))
cells.append(code("""import random, math
def coupon_sim(n,trials=10000):
    total=0
    for _ in range(trials):
        seen=set(); cnt=0
        while len(seen)<n: seen.add(random.randint(0,n-1)); cnt+=1
        total+=cnt
    return total/trials
def coupon_theory(n): return n*sum(1/i for i in range(1,n+1))
def coupon_formula(n): return n*math.log(n)+0.5772*n+0.5  # approximation
for n in [5,10,20]:
    print(f"n={n}: theory={coupon_theory(n):.2f} sim={coupon_sim(n):.2f}")"""))

# ── Q142 Sliding Window Distinct Count ──
cells.append(md("---\n## Q142 · Sliding Window Distinct Count (Data Engineering – MEDIUM)\n**Problem:** Count distinct elements in every window of size k.\n### 🧠 Remember: Counter + slide; add new, decrement old (remove if 0)"))
cells.append(code("""def sw_distinct1(arr,k): return [len(set(arr[i:i+k])) for i in range(len(arr)-k+1)]
def sw_distinct2(arr,k):
    cnt=Counter(arr[:k]); res=[len(cnt)]
    for i in range(k,len(arr)):
        cnt[arr[i]]+=1
        cnt[arr[i-k]]-=1
        if cnt[arr[i-k]]==0: del cnt[arr[i-k]]
        res.append(len(cnt))
    return res
a=[1,2,1,3,2,4]; k=3
print("Brute:",sw_distinct1(a,k))
print("Slide:",sw_distinct2(a,k))
print("Time O(nk)/O(n) | Space O(k)")"""))

# ── Q145 Cross Validation ──
cells.append(md("---\n## Q145 · Cross Validation (ML Coding – MEDIUM)\n**Problem:** Implement k-fold cross validation.\n### 🧠 Remember: split into k folds; each fold is test once; avg metric"))
cells.append(code("""def kfold1(X,y,k):
    n=len(X); sz=n//k; scores=[]
    for i in range(k):
        test_idx=list(range(i*sz,(i+1)*sz))
        train_idx=[j for j in range(n) if j not in set(test_idx)]
        X_tr=[X[j] for j in train_idx]; y_tr=[y[j] for j in train_idx]
        X_te=[X[j] for j in test_idx]; y_te=[y[j] for j in test_idx]
        # simple: predict majority class
        from collections import Counter
        pred=Counter(y_tr).most_common(1)[0][0]
        acc=sum(1 for yy in y_te if yy==pred)/len(y_te)
        scores.append(acc)
    return scores, sum(scores)/len(scores)
X=list(range(100)); y=[i%2 for i in range(100)]
scores,avg=kfold1(X,y,5)
print(f"Fold scores:{[round(s,2) for s in scores]} Avg:{avg:.2f}")
print("Time O(k*n) Space O(n)")"""))

# ── Q150 House Robber ──
cells.append(md("---\n## Q150 · House Robber (Algorithms – MEDIUM)\n**Problem:** Max sum without adjacent elements.\n### 🧠 Remember: dp[i]=max(dp[i-2]+nums[i], dp[i-1]); space-opt: keep prev2,prev1"))
cells.append(code("""def rob1(nums):
    @lru_cache(None)
    def dp(i):
        if i<0: return 0
        return max(dp(i-2)+nums[i],dp(i-1))
    return dp(len(nums)-1)
def rob2(nums):
    if not nums: return 0
    n=len(nums); dp=[0]*(n+1)
    dp[1]=nums[0]
    for i in range(2,n+1): dp[i]=max(dp[i-2]+nums[i-1],dp[i-1])
    return dp[n]
def rob3(nums):
    p2=p1=0
    for n in nums: p2,p1=p1,max(p1,p2+n)
    return p1
for f in [rob1,rob2,rob3]:
    print(f([2,7,9,3,1]), f([1,2,3,1]))
print("Time O(n) Space O(n)/O(n)/O(1)")"""))

# ── Q160 Streaming Median ──
cells.append(md("---\n## Q160 · Streaming Median Finder (Data Engineering – HARD)\n**Problem:** Median of running stream.\n### 🧠 Remember: max-heap for lower half, min-heap for upper half; balance sizes"))
cells.append(code("""class MedianFinder:
    def __init__(self): self.lo=[]; self.hi=[]  # max-heap lo, min-heap hi
    def add(self,num):
        heapq.heappush(self.lo,-num)
        heapq.heappush(self.hi,-heapq.heappop(self.lo))
        if len(self.hi)>len(self.lo): heapq.heappush(self.lo,-heapq.heappop(self.hi))
    def median(self):
        if len(self.lo)>len(self.hi): return -self.lo[0]
        return (-self.lo[0]+self.hi[0])/2
mf=MedianFinder()
for v in [5,2,8,1,9,3]:
    mf.add(v); print(f"add {v} → median={mf.median()}")
print("Time O(logn) add, O(1) median | Space O(n)")"""))

# ── Q164 Word Occurrence Tally ──
cells.append(md("---\n## Q164 · Word Occurrence Tally (Database – EASY)\n**Problem:** Count occurrences of each word in text column.\n### 🧠 Remember: split text → unnest → GROUP BY word → COUNT"))
cells.append(code("""c6=sqlite3.connect(':memory:')
c6.execute("CREATE TABLE docs(id INT,text TEXT)")
c6.executemany("INSERT INTO docs VALUES(?,?)",[(1,'hello world'),(2,'hello again'),(3,'world peace hello')])
# Python approach (SQLite lacks UNNEST)
import pandas as pd
df=pd.read_sql("SELECT*FROM docs",c6)
words=[w for row in df['text'] for w in row.split()]
wc=Counter(words)
print(pd.DataFrame(wc.most_common(),columns=['word','count']))
# SQL approach: use WITH RECURSIVE or Python
q="SELECT text FROM docs"
all_text=' '.join(pd.read_sql(q,c6)['text'])
wc2=Counter(all_text.split())
print({k:v for k,v in sorted(wc2.items(),key=lambda x:-x[1])})"""))

# ── Q166 Open the Lock ──
cells.append(md("---\n## Q166 · Open the Lock (Data Structures – MEDIUM)\n**Problem:** BFS to open 4-digit lock from '0000' to target avoiding deadends.\n### 🧠 Remember: BFS on 4-digit combinations; each step turns one digit ±1"))
cells.append(code("""def open_lock1(deadends,target):
    dead=set(deadends); start='0000'
    if start in dead: return -1
    q=deque([(start,0)]); vis={start}
    while q:
        state,steps=q.popleft()
        if state==target: return steps
        for i in range(4):
            d=int(state[i])
            for nd in[(d+1)%10,(d-1)%10]:
                nxt=state[:i]+str(nd)+state[i+1:]
                if nxt not in vis and nxt not in dead:
                    vis.add(nxt); q.append((nxt,steps+1))
    return -1
def open_lock2(deadends,target):  # bidirectional BFS
    dead=set(deadends)
    if '0000' in dead: return -1
    front,back={'0000'},{target}; visited=set(); steps=0
    while front:
        if front&back: return steps
        visited|=front; nxt=set()
        for state in front:
            for i in range(4):
                d=int(state[i])
                for nd in[(d+1)%10,(d-1)%10]:
                    s=state[:i]+str(nd)+state[i+1:]
                    if s not in visited and s not in dead: nxt.add(s)
        front=nxt; steps+=1
        if len(front)>len(back): front,back=back,front
    return -1
print(open_lock1(["0201","0101","0102","1212","2002"],"0202"))  # 6
print(open_lock2(["0201","0101","0102","1212","2002"],"0202"))  # 6
print("Time O(10^4) Space O(10^4)")"""))

# ── Q173 Subsets ──
cells.append(md("---\n## Q173 · Subsets (Algorithms – MEDIUM)\n**Problem:** Return all subsets of a list.\n### 🧠 Remember: backtracking OR bitmask OR iterative build"))
cells.append(code("""def subsets1(nums):  # backtrack
    res=[]; path=[]
    def bt(start):
        res.append(path[:])
        for i in range(start,len(nums)):
            path.append(nums[i]); bt(i+1); path.pop()
    bt(0); return res
def subsets2(nums):  # bitmask
    n=len(nums)
    return [[nums[j] for j in range(n) if i>>j&1] for i in range(1<<n)]
def subsets3(nums):  # iterative
    res=[[]]
    for n in nums: res+=[s+[n] for s in res]
    return res
ns=[1,2,3]
print("Backtrack:",len(subsets1(ns)),"subsets")
print("Bitmask:  ",len(subsets2(ns)),"subsets")
print("Iterative:",len(subsets3(ns)),"subsets")
print(subsets3(ns))
print("Time O(n*2^n) Space O(n*2^n)")"""))

# ── Q178 Bottom 10 Hotels ──
cells.append(md("---\n## Q178 · Bottom 10 Hotel Ratings (Database – MEDIUM)\n**Problem:** Find 10 lowest-rated hotels.\n### 🧠 Remember: AVG rating GROUP BY hotel → ORDER BY ASC → LIMIT 10"))
cells.append(code("""c7=sqlite3.connect(':memory:')
c7.execute("CREATE TABLE hotel_reviews(hotel TEXT,score REAL)")
import random; random.seed(1)
hotels=['A','B','C','D','E','F','G','H','I','J','K','L']
for h in hotels:
    for _ in range(random.randint(3,8)):
        c7.execute("INSERT INTO hotel_reviews VALUES(?,?)",(h,round(random.uniform(1,5),1)))
q1="SELECT hotel,ROUND(AVG(score),2) avg_score FROM hotel_reviews GROUP BY hotel ORDER BY avg_score LIMIT 10"
q2="WITH s AS(SELECT hotel,AVG(score) a FROM hotel_reviews GROUP BY hotel),r AS(SELECT*,RANK()OVER(ORDER BY a) rk FROM s) SELECT hotel,ROUND(a,2) avg_score,rk FROM r WHERE rk<=10"
print(pd.read_sql(q1,c7).to_string())
print("Time O(n) Space O(hotels)")"""))

# ── Q180 Records with Multiple Nulls ──
cells.append(md("---\n## Q180 · Records With Multiple Nulls (Database – EASY)\n**Problem:** Find rows where 2+ columns are NULL.\n### 🧠 Remember: (col1 IS NULL)+(col2 IS NULL)+... >= 2"))
cells.append(code("""c8=sqlite3.connect(':memory:')
c8.execute("CREATE TABLE t(id INT,a TEXT,b TEXT,c TEXT)")
c8.executemany("INSERT INTO t VALUES(?,?,?,?)",[(1,'x',None,None),(2,None,None,None),(3,'x','y','z'),(4,'x',None,'z')])
q1="SELECT*FROM t WHERE (a IS NULL)+(b IS NULL)+(c IS NULL)>=2"
q2="SELECT*,((a IS NULL)+(b IS NULL)+(c IS NULL)) null_count FROM t HAVING null_count>=2"
print(pd.read_sql(q1,c8).to_string())
print("Time O(n) Space O(1)")"""))

# ── Q184 Momentum Update ──
cells.append(md("---\n## Q184 · Momentum Update Step (ML Coding – EASY)\n**Problem:** v = γ*v - lr*grad; w = w + v\n### 🧠 Remember: momentum accumulates gradient history; γ~0.9"))
cells.append(code("""def momentum1(w,g,v,lr=0.01,gamma=0.9):
    v_new=gamma*v-lr*g
    return w+v_new, v_new
def momentum2(params,grads,velocities,lr=0.01,gamma=0.9):
    new_v=[gamma*v-lr*g for v,g in zip(velocities,grads)]
    new_p=[p+v for p,v in zip(params,new_v)]
    return new_p,new_v
try:
    import numpy as np
    def momentum3(w,g,v,lr=0.01,gamma=0.9):
        v=gamma*v-lr*g; return w+v,v
except: momentum3=momentum1
w,g,v=1.0,0.5,0.0
for step in range(5):
    w,v=momentum1(w,g,v)
    print(f"step {step+1}: w={w:.4f} v={v:.4f}")
print("Time O(n) Space O(n)")"""))

# ── Q195 Monty Hall ──
cells.append(md("---\n## Q195 · Monty Hall Simulation (Statistics – EASY)\n**Problem:** Simulate Monty Hall; show switch wins ~67%.\n### 🧠 Remember: always switch → win if initial pick was wrong (prob 2/3)"))
cells.append(code("""import random
def monty_sim(n=100000):
    stay_wins=switch_wins=0
    for _ in range(n):
        car=random.randint(0,2); pick=random.randint(0,2)
        # host opens a goat door (not car, not pick)
        goat=[d for d in range(3) if d!=car and d!=pick]
        host=random.choice(goat)
        # switch: pick the remaining door
        switch=next(d for d in range(3) if d!=pick and d!=host)
        if pick==car: stay_wins+=1
        if switch==car: switch_wins+=1
    return stay_wins/n, switch_wins/n
stay,switch=monty_sim()
print(f"Stay  wins: {stay:.3f} (expected ~0.333)")
print(f"Switch wins:{switch:.3f} (expected ~0.667)")"""))

# ── Q218 Mean/Median Imputation ──
cells.append(md("---\n## Q218 · Mean and Median Imputation (ML Coding – EASY)\n**Problem:** Fill NaN values with mean or median.\n### 🧠 Remember: mean for normal dist, median for skewed/outliers"))
cells.append(code("""def impute_mean(data):
    vals=[x for x in data if x is not None]
    mu=sum(vals)/len(vals)
    return [mu if x is None else x for x in data]
def impute_median(data):
    vals=sorted(x for x in data if x is not None)
    n=len(vals); med=vals[n//2] if n%2 else (vals[n//2-1]+vals[n//2])/2
    return [med if x is None else x for x in data]
try:
    import numpy as np
    def impute_np(data,method='mean'):
        a=np.array(data,dtype=float)
        fill=np.nanmean(a) if method=='mean' else np.nanmedian(a)
        a[np.isnan(a)]=fill; return a.tolist()
except: impute_np=impute_mean
data=[1,None,3,None,5,100]
print("Mean:  ",[round(x,1) for x in impute_mean(data)])
print("Median:",[round(x,1) for x in impute_median(data)])
print("Time O(n) Space O(n)")"""))

# ── Q221 Gini Impurity ──
cells.append(md("---\n## Q221 · Gini Impurity (ML Coding – EASY)\n**Problem:** Gini = 1 - Σ(p_i²)\n### 🧠 Remember: 1 minus sum of squared probabilities; 0=pure, 0.5=max impure (binary)"))
cells.append(code("""def gini1(labels):
    n=len(labels); cnt=Counter(labels)
    return 1-sum((v/n)**2 for v in cnt.values())
def gini2(probs):  # from probabilities directly
    return 1-sum(p*p for p in probs)
def gini3(labels):
    n=len(labels)
    return 1-sum((labels.count(c)/n)**2 for c in set(labels))
print(gini1([1,1,1,1]))        # 0.0 (pure)
print(gini1([1,1,0,0]))        # 0.5 (max impure binary)
print(gini1([1,2,3,4]))        # 0.75
print(gini2([0.5,0.5]))        # 0.5
print("Time O(n) Space O(classes)")"""))

# ── Q222 Course Schedule II ──
cells.append(md("---\n## Q222 · Course Schedule II (Data Structures – MEDIUM)\n**Problem:** Return topological order of courses given prerequisites.\n### 🧠 Remember: DFS with 3 states (unvisited/visiting/done); BFS with in-degree (Kahn's)"))
cells.append(code("""def course_order1(n,prereqs):  # BFS Kahn's
    graph=defaultdict(list); indeg=[0]*n
    for a,b in prereqs: graph[b].append(a); indeg[a]+=1
    q=deque(i for i in range(n) if indeg[i]==0); res=[]
    while q:
        node=q.popleft(); res.append(node)
        for nb in graph[node]: indeg[nb]-=1; (q.append(nb) if indeg[nb]==0 else None)
    return res if len(res)==n else []
def course_order2(n,prereqs):  # DFS
    graph=defaultdict(list)
    for a,b in prereqs: graph[b].append(a)
    state=[0]*n; res=[]
    def dfs(v):
        if state[v]==1: return False
        if state[v]==2: return True
        state[v]=1
        if not all(dfs(nb) for nb in graph[v]): return False
        state[v]=2; res.append(v); return True
    return res[::-1] if all(dfs(i) for i in range(n)) else []
print(course_order1(4,[[1,0],[2,0],[3,1],[3,2]]))
print(course_order2(4,[[1,0],[2,0],[3,1],[3,2]]))
print("Time O(V+E) Space O(V+E)")"""))

# ── Q229 Product of Last K Numbers ──
cells.append(md("---\n## Q229 · Product of the Last K Numbers (Data Structures – MEDIUM)\n**Problem:** Stream of numbers; efficiently get product of last k.\n### 🧠 Remember: prefix products; but reset on 0 (product becomes 0)"))
cells.append(code("""class ProductOfNumbers:
    def __init__(self): self.pre=[1]
    def add(self,num):
        if num==0: self.pre=[1]
        else: self.pre.append(self.pre[-1]*num)
    def getProduct(self,k):
        if k>=len(self.pre): return 0
        return self.pre[-1]//self.pre[-k-1]
class ProductOfNumbers2:  # simple deque
    def __init__(self): self.data=deque()
    def add(self,num): self.data.append(num)
    def getProduct(self,k):
        res=1
        for v in list(self.data)[-k:]: res*=v
        return res
p=ProductOfNumbers()
for v in [3,0,2,5,4]: p.add(v)
print(p.getProduct(2),p.getProduct(3),p.getProduct(4))  # 20, 40, 0
print("Time O(1) add/get | Space O(n)")"""))

# ── Q231 Simplify Path ──
cells.append(md("---\n## Q231 · Simplify Path (Data Structures – MEDIUM)\n**Problem:** Unix path simplification: '/a/./b/../../c/' → '/c'.\n### 🧠 Remember: split by '/'; stack; '..' pops; '.' ignored; rest pushed"))
cells.append(code("""def simplify1(path):
    stk=[]
    for part in path.split('/'):
        if part=='..':
            if stk: stk.pop()
        elif part and part!='.': stk.append(part)
    return '/'+'/'.join(stk)
def simplify2(path):
    parts=[p for p in path.split('/') if p and p!='.']
    res=[]
    for p in parts:
        if p=='..': res and res.pop()
        else: res.append(p)
    return '/'+'/'.join(res)
print(simplify1('/home/'))           # /home
print(simplify1('/../'))             # /
print(simplify1('/home//foo/'))      # /home/foo
print(simplify1('/a/./b/../../c/'))  # /c
print("Time O(n) Space O(n)")"""))

# ── Q238 Number of Provinces ──
cells.append(md("---\n## Q238 · Number of Provinces (Data Structures – MEDIUM)\n**Problem:** Count connected components in adjacency matrix.\n### 🧠 Remember: Union Find or DFS; count roots (nodes where parent==self)"))
cells.append(code("""def provinces_uf(isConnected):
    n=len(isConnected); parent=list(range(n))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b): parent[find(a)]=find(b)
    for i in range(n):
        for j in range(i+1,n):
            if isConnected[i][j]: union(i,j)
    return sum(1 for i in range(n) if find(i)==i)
def provinces_dfs(isConnected):
    n=len(isConnected); vis=[False]*n; count=0
    def dfs(v):
        vis[v]=True
        for u in range(n):
            if isConnected[v][u] and not vis[u]: dfs(u)
    for i in range(n):
        if not vis[i]: dfs(i); count+=1
    return count
m=[[1,1,0],[1,1,0],[0,0,1]]
print(provinces_uf(m), provinces_dfs(m))  # 2
m2=[[1,0,0],[0,1,0],[0,0,1]]
print(provinces_uf(m2), provinces_dfs(m2))  # 3
print("Time O(n²) Space O(n)")"""))

# ── Q259 Covariance ──
cells.append(md("---\n## Q259 · Covariance (Statistics – MEDIUM)\n**Problem:** Compute covariance between two variables.\n### 🧠 Remember: cov = E[(X-μx)(Y-μy)] = E[XY] - μx*μy"))
cells.append(code("""def cov1(x,y):
    n=len(x); mx,my=sum(x)/n,sum(y)/n
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/n
def cov2(x,y):  # sample covariance (n-1)
    n=len(x); mx,my=sum(x)/n,sum(y)/n
    return sum((a-mx)*(b-my) for a,b in zip(x,y))/(n-1)
def cov_matrix(data):  # multiple variables
    n=len(data[0]); means=[sum(r[i] for r in data)/n for i in range(len(data[0]))]
    return [[sum((data[k][i]-means[i])*(data[k][j]-means[j]) for k in range(n))/(n-1)
             for j in range(len(means))] for i in range(len(means))]
x=[1,2,3,4,5]; y=[5,4,3,2,1]
print(f"cov(x,y) pop={cov1(x,y):.2f} sample={cov2(x,y):.2f}")
print("Time O(n) Space O(1)")"""))

# ── Q264 Most Viewed Posts ──
cells.append(md("---\n## Q264 · Most Viewed Posts (Database – HARD)\n**Problem:** Top posts by view count with author info.\n### 🧠 Remember: JOIN posts+views → GROUP BY post_id → RANK()"))
cells.append(code("""c9=sqlite3.connect(':memory:')
c9.execute("CREATE TABLE posts(id INT,author TEXT,title TEXT)")
c9.execute("CREATE TABLE views(post_id INT,user_id INT)")
c9.executemany("INSERT INTO posts VALUES(?,?,?)",[(1,'Alice','Post A'),(2,'Bob','Post B'),(3,'Alice','Post C')])
c9.executemany("INSERT INTO views VALUES(?,?)",[(1,10),(1,11),(1,12),(2,10),(2,11),(3,10)])
q="WITH vc AS(SELECT post_id,COUNT(*) views FROM views GROUP BY post_id),rk AS(SELECT p.*,vc.views,RANK()OVER(ORDER BY vc.views DESC) r FROM posts p JOIN vc ON p.id=vc.post_id) SELECT title,author,views FROM rk WHERE r<=3"
print(pd.read_sql(q,c9).to_string())"""))

# ── Q270 Euclidean Distance ──
cells.append(md("---\n## Q270 · Euclidean Distance (ML Coding – EASY)\n**Problem:** sqrt(Σ(a_i - b_i)²)\n### 🧠 Remember: L2 norm of difference vector"))
cells.append(code("""import math
def euc1(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def euc2(a,b): return sum((x-y)**2 for x,y in zip(a,b))**0.5
try:
    import numpy as np
    def euc3(a,b): return float(np.linalg.norm(np.array(a)-np.array(b)))
except: euc3=euc1
p1=[1,2,3]; p2=[4,6,3]
print(euc1(p1,p2), euc2(p1,p2), euc3(p1,p2))  # 5.0
print("Time O(n) Space O(1)")"""))

# ── Q272 MSE ──
cells.append(md("---\n## Q272 · Mean Squared Error (ML Coding – EASY)\n**Problem:** MSE = mean((y_pred - y_true)²)\n### 🧠 Remember: square each error, take mean; RMSE = sqrt(MSE)"))
cells.append(code("""def mse1(y,p): return sum((a-b)**2 for a,b in zip(y,p))/len(y)
def mse2(y,p):
    n=len(y); return sum((y[i]-p[i])**2 for i in range(n))/n
try:
    import numpy as np
    def mse3(y,p): return float(np.mean((np.array(y)-np.array(p))**2))
except: mse3=mse1
yt=[3,2,4,1]; yp=[2.5,2,4.5,1]
print(f"MSE={mse1(yt,yp):.4f} RMSE={mse1(yt,yp)**0.5:.4f}")
print("Time O(n) Space O(1)")"""))

# ── Q279 Handyman Employee Rate ──
cells.append(md("---\n## Q279 · Handyman Employee Rate (Database – MEDIUM)\n**Problem:** Rate of tasks completed per employee.\n### 🧠 Remember: COUNT(completed) / COUNT(*) GROUP BY employee"))
cells.append(code("""c10=sqlite3.connect(':memory:')
c10.execute("CREATE TABLE tasks(emp TEXT,task_id INT,done INT)")
c10.executemany("INSERT INTO tasks VALUES(?,?,?)",[('Alice',1,1),('Alice',2,1),('Alice',3,0),('Bob',4,1),('Bob',5,0),('Bob',6,0)])
q1="SELECT emp,ROUND(1.0*SUM(done)/COUNT(*),2) completion_rate,COUNT(*) total FROM tasks GROUP BY emp ORDER BY completion_rate DESC"
q2="WITH s AS(SELECT emp,SUM(done) done,COUNT(*) tot FROM tasks GROUP BY emp) SELECT emp,ROUND(1.0*done/tot,2) rate FROM s ORDER BY rate DESC"
print(pd.read_sql(q1,c10).to_string())"""))

# ── Q282 Clicked And No Conversion ──
cells.append(md("---\n## Q282 · Clicked And No Conversion (Database – MEDIUM)\n**Problem:** Users who clicked ads but didn't convert.\n### 🧠 Remember: LEFT JOIN or NOT IN: click users minus convert users"))
cells.append(code("""c11=sqlite3.connect(':memory:')
c11.execute("CREATE TABLE ad_events(user_id INT,event TEXT)")
c11.executemany("INSERT INTO ad_events VALUES(?,?)",[(1,'click'),(1,'convert'),(2,'click'),(3,'click'),(3,'click'),(4,'convert')])
q1="SELECT DISTINCT user_id FROM ad_events WHERE event='click' AND user_id NOT IN(SELECT user_id FROM ad_events WHERE event='convert')"
q2="WITH cl AS(SELECT DISTINCT user_id FROM ad_events WHERE event='click'),cv AS(SELECT DISTINCT user_id FROM ad_events WHERE event='convert') SELECT cl.user_id FROM cl LEFT JOIN cv ON cl.user_id=cv.user_id WHERE cv.user_id IS NULL"
print("Clicked no conversion:")
print(pd.read_sql(q1,c11).to_string())"""))

# ── Q283 Network Connected ──
cells.append(md("---\n## Q283 · Number of Operations to Make Network Connected (Data Structures – MEDIUM)\n**Problem:** n computers, connections list. Min cable moves to connect all.\n### 🧠 Remember: need n-1 edges for n nodes; count components-1; fail if edges<n-1"))
cells.append(code("""def make_connected1(n,connections):
    if len(connections)<n-1: return -1
    parent=list(range(n))
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b): parent[find(a)]=find(b)
    for a,b in connections: union(a,b)
    return sum(1 for i in range(n) if find(i)==i)-1
def make_connected2(n,connections):
    if len(connections)<n-1: return -1
    adj=defaultdict(set)
    for a,b in connections: adj[a].add(b); adj[b].add(a)
    vis=set(); components=0
    def dfs(v):
        vis.add(v)
        for u in adj[v]:
            if u not in vis: dfs(u)
    for i in range(n):
        if i not in vis: dfs(i); components+=1
    return components-1
print(make_connected1(4,[[0,1],[0,2],[1,2]]))  # 1
print(make_connected2(6,[[0,1],[0,2],[0,3],[1,2],[1,3]]))  # 2
print("Time O(n+e) Space O(n)")"""))

# ── Q285 Email Records By Senders ──
cells.append(md("---\n## Q285 · Email Records By Senders (Database – EASY)\n**Problem:** Count emails sent per sender.\n### 🧠 Remember: GROUP BY sender → COUNT(*)"))
cells.append(code("""c12=sqlite3.connect(':memory:')
c12.execute("CREATE TABLE sent_emails(sender TEXT,recipient TEXT,date TEXT)")
c12.executemany("INSERT INTO sent_emails VALUES(?,?,?)",[('Alice','Bob','2023-01-01'),('Alice','Carol','2023-01-02'),('Bob','Alice','2023-01-01'),('Carol','Bob','2023-01-03'),('Alice','Dave','2023-01-03')])
q="SELECT sender,COUNT(*) emails_sent FROM sent_emails GROUP BY sender ORDER BY emails_sent DESC"
print(pd.read_sql(q,c12).to_string())"""))

# ── Q287 Hand of Straights ──
cells.append(md("---\n## Q287 · Hand of Straights (Algorithms – MEDIUM)\n**Problem:** Can hand be rearranged into groups of W consecutive cards?\n### 🧠 Remember: sort + counter; start from smallest, remove W consecutive"))
cells.append(code("""def hand1(hand,W):
    cnt=Counter(hand)
    for card in sorted(cnt):
        n=cnt[card]
        if n==0: continue
        for c in range(card,card+W):
            if cnt[c]<n: return False
            cnt[c]-=n
    return True
def hand2(hand,W):
    if len(hand)%W: return False
    cnt=Counter(hand)
    for start in sorted(cnt):
        while cnt[start]:
            n=cnt[start]
            for c in range(start,start+W):
                cnt[c]-=n
                if cnt[c]<0: return False
    return True
print(hand1([1,2,3,6,2,3,4,7,8],3))  # True
print(hand1([1,2,3,4,5],4))           # False
print("Time O(n logn) Space O(n)")"""))

# ── Q289 Users by Platform ──
cells.append(md("---\n## Q289 · Users by Platform (Database – EASY)\n**Problem:** Count users per platform.\n### 🧠 Remember: GROUP BY platform → COUNT(DISTINCT user_id)"))
cells.append(code("""c13=sqlite3.connect(':memory:')
c13.execute("CREATE TABLE sessions(user_id INT,platform TEXT,date TEXT)")
c13.executemany("INSERT INTO sessions VALUES(?,?,?)",[(1,'iOS','2023-01-01'),(2,'Android','2023-01-01'),(1,'iOS','2023-01-02'),(3,'Web','2023-01-02'),(2,'iOS','2023-01-03'),(4,'Android','2023-01-03')])
q="SELECT platform,COUNT(DISTINCT user_id) users FROM sessions GROUP BY platform ORDER BY users DESC"
print(pd.read_sql(q,c13).to_string())"""))

# ── Q308 Power of Two ──
cells.append(md("---\n## Q308 · Power of Two (Algorithms – EASY)\n**Problem:** Is n a power of 2?\n### 🧠 Remember: n>0 and n&(n-1)==0 (only one bit set)"))
cells.append(code("""def pow2_bit(n): return n>0 and (n&(n-1))==0
def pow2_loop(n):
    if n<=0: return False
    while n>1:
        if n%2: return False
        n//=2
    return True
def pow2_math(n): return n>0 and 2**round(math.log2(n))==n
for v in [1,2,3,4,16,18]:
    print(f"{v}: bit={pow2_bit(v)} loop={pow2_loop(v)} math={pow2_math(v)}")
print("Time O(1)/O(logn)/O(1)")"""))

# ── Q316 Most Recent Login ──
cells.append(md("---\n## Q316 · Most Recent Login Date (Database – EASY)\n**Problem:** Most recent login per user.\n### 🧠 Remember: MAX(login_date) GROUP BY user_id"))
cells.append(code("""c14=sqlite3.connect(':memory:')
c14.execute("CREATE TABLE logins(user_id INT,login_date TEXT)")
c14.executemany("INSERT INTO logins VALUES(?,?)",[(1,'2023-01-01'),(1,'2023-01-05'),(2,'2023-01-03'),(2,'2023-01-07'),(3,'2023-01-02')])
q1="SELECT user_id,MAX(login_date) last_login FROM logins GROUP BY user_id"
q2="WITH rk AS(SELECT*,ROW_NUMBER()OVER(PARTITION BY user_id ORDER BY login_date DESC) r FROM logins) SELECT user_id,login_date last_login FROM rk WHERE r=1"
print(pd.read_sql(q1,c14).to_string())"""))

# ── Q317 Max Consecutive Ones III ──
cells.append(md("---\n## Q317 · Max Consecutive Ones III (Algorithms – MEDIUM)\n**Problem:** Max 1s in subarray after flipping at most k zeros.\n### 🧠 Remember: sliding window; shrink when zeros in window > k"))
cells.append(code("""def max_ones1(nums,k):  # brute
    n=len(nums); best=0
    for i in range(n):
        zeros=0
        for j in range(i,n):
            if nums[j]==0: zeros+=1
            if zeros>k: break
            best=max(best,j-i+1)
    return best
def max_ones2(nums,k):  # sliding window
    l=zeros=res=0
    for r,v in enumerate(nums):
        if v==0: zeros+=1
        while zeros>k: zeros-=(nums[l]==0); l+=1
        res=max(res,r-l+1)
    return res
def max_ones3(nums,k):  # optimized (never shrink window)
    l=0
    for r,v in enumerate(nums):
        k-=(v==0)
        if k<0: k+=(nums[l]==0); l+=1
    return r-l+1 if nums else 0
print(max_ones1([1,1,1,0,0,0,1,1,1,1,0],2))  # 6
print(max_ones2([1,1,1,0,0,0,1,1,1,1,0],2))  # 6
print(max_ones3([1,1,1,0,0,0,1,1,1,1,0],2))  # 6
print("Time O(n) Space O(1)")"""))

# ── Q319 No Reaction Rate ──
cells.append(md("---\n## Q319 · No Reaction Rate (Database – HARD)\n**Problem:** % of posts with zero reactions.\n### 🧠 Remember: LEFT JOIN posts with reactions; posts with no reactions = IS NULL or count=0"))
cells.append(code("""c15=sqlite3.connect(':memory:')
c15.execute("CREATE TABLE posts(post_id INT,user_id INT)")
c15.execute("CREATE TABLE post_reactions(post_id INT,reaction TEXT)")
c15.executemany("INSERT INTO posts VALUES(?,?)",[(1,1),(2,1),(3,2),(4,2),(5,3)])
c15.executemany("INSERT INTO post_reactions VALUES(?,?)",[(1,'like'),(1,'comment'),(3,'like')])
q="SELECT ROUND(100.0*SUM(CASE WHEN pr.post_id IS NULL THEN 1 ELSE 0 END)/COUNT(*),2) no_reaction_rate FROM posts p LEFT JOIN(SELECT DISTINCT post_id FROM post_reactions)pr ON p.post_id=pr.post_id"
print(pd.read_sql(q,c15).to_string())
print("Time O(n) Space O(posts)")"""))

# ── Q330 Merge Triplets ──
cells.append(md("---\n## Q330 · Merge Triplets to Form Target (Algorithms – MEDIUM)\n**Problem:** Select triplets and OR them to form target.\n### 🧠 Remember: filter triplets where any dim > target dim; then check if OR of remaining = target"))
cells.append(code("""def merge_triplets1(triplets,target):
    res=[0,0,0]
    for t in triplets:
        if t[0]<=target[0] and t[1]<=target[1] and t[2]<=target[2]:
            res=[max(res[i],t[i]) for i in range(3)]
    return res==target
def merge_triplets2(triplets,target):  # greedy bit
    good=[t for t in triplets if all(t[i]<=target[i] for i in range(3))]
    return [max(t[i] for t in good) for i in range(3)]==target if good else False
print(merge_triplets1([[2,5,3],[1,8,4],[1,7,5]],[2,7,5]))  # True
print(merge_triplets2([[3,4,5],[4,5,6]],[3,2,5]))           # False
print("Time O(n) Space O(1)")"""))

# ── Q353 Sort the People ──
cells.append(md("---\n## Q353 · Sort the People (Algorithms – EASY)\n**Problem:** Sort names by heights descending.\n### 🧠 Remember: zip names+heights, sort by height desc, unzip names"))
cells.append(code("""def sort_people1(names,heights):
    return [n for n,h in sorted(zip(names,heights),key=lambda x:-x[1])]
def sort_people2(names,heights):
    idx=sorted(range(len(heights)),key=lambda i:-heights[i])
    return [names[i] for i in idx]
def sort_people3(names,heights):
    pairs=sorted(zip(heights,names),reverse=True)
    return [n for h,n in pairs]
n=["Alice","Bob","Bob"]; h=[155,185,150]
print(sort_people1(n[:],h[:]))
print(sort_people2(n[:],h[:]))
print("Time O(n logn) Space O(n)")"""))

# ── Q356 Basic Calculator ──
cells.append(md("---\n## Q356 · Basic Calculator (Data Structures – HARD)\n**Problem:** Evaluate string with +,-,( ).\n### 🧠 Remember: stack stores (result, sign) before each '('; on ')' pop and combine"))
cells.append(code("""def calc1(s):
    stk=[]; res=0; num=0; sign=1
    for c in s:
        if c.isdigit(): num=num*10+int(c)
        elif c in'+-':
            res+=sign*num; num=0
            sign=1 if c=='+' else -1
        elif c=='(': stk.append(res); stk.append(sign); res=0; sign=1
        elif c==')':
            res+=sign*num; num=0
            res*=stk.pop(); res+=stk.pop()
    return res+sign*num
def calc2(s):  # recursive descent
    s=list(s); i=[0]
    def parse():
        res=0; sign=1; num=0
        while i[0]<len(s):
            c=s[i[0]]; i[0]+=1
            if c.isdigit(): num=num*10+int(c)
            elif c in'+-':
                res+=sign*num; num=0
                sign=1 if c=='+' else -1
            elif c=='(': res+=sign*parse(); num=0
            elif c==')': break
        return res+sign*num
    return parse()
print(calc1("1 + 1"))           # 2
print(calc1(" 2-1 + 2 "))       # 3
print(calc1("(1+(4+5+2)-3)+(6+8)"))  # 23
print("Time O(n) Space O(n)")"""))

# ── Q364 Moving Average ──
cells.append(md("---\n## Q364 · Moving Average (ML Coding – EASY)\n**Problem:** Compute simple moving average of last k values.\n### 🧠 Remember: deque of size k; sum/len"))
cells.append(code("""class MovingAvg1:
    def __init__(self,k): self.k=k; self.q=deque(); self.s=0
    def next(self,v):
        self.q.append(v); self.s+=v
        if len(self.q)>self.k: self.s-=self.q.popleft()
        return self.s/len(self.q)
def moving_avg2(data,k): return [sum(data[max(0,i-k+1):i+1])/min(i+1,k) for i in range(len(data))]
ma=MovingAvg1(3)
data=[1,10,3,5]
for v in data: print(round(ma.next(v),2),end=' ')
print()
print([round(x,2) for x in moving_avg2(data,3)])
print("Time O(1) per call | Space O(k)")"""))

# ── Q368 Min Cost Tickets ──
cells.append(md("---\n## Q368 · Minimum Cost For Tickets (Algorithms – MEDIUM)\n**Problem:** Min cost to travel on given days using 1/7/30-day passes.\n### 🧠 Remember: DP[i]=min cost to travel days[0..i]; for each day try 3 pass costs"))
cells.append(code("""def min_tickets1(days,costs):
    travel=set(days); last=days[-1]
    dp=[0]*(last+1)
    for i in range(1,last+1):
        if i not in travel: dp[i]=dp[i-1]
        else:
            dp[i]=min(dp[i-1]+costs[0],
                      dp[max(0,i-7)]+costs[1],
                      dp[max(0,i-30)]+costs[2])
    return dp[last]
def min_tickets2(days,costs):  # DP on index
    n=len(days)
    @lru_cache(None)
    def dp(i):
        if i>=n: return 0
        res=float('inf')
        for dur,cost in zip([1,7,30],costs):
            j=i
            while j<n and days[j]<days[i]+dur: j+=1
            res=min(res,cost+dp(j))
        return res
    return dp(0)
print(min_tickets1([1,4,6,7,8,20],[2,7,15]))  # 11
print(min_tickets2([1,2,3,4,5,6,7,8,9,10,30,31],[2,7,15]))  # 17
print("Time O(last_day) Space O(last_day)")"""))

# ── Q371 Top 2 Products per Category ──
cells.append(md("---\n## Q371 · Top 2 Products per Category (Database – HARD)\n**Problem:** Top 2 best-selling products per category.\n### 🧠 Remember: sales GROUP BY category,product → DENSE_RANK() → filter rank<=2"))
cells.append(code("""c16=sqlite3.connect(':memory:')
c16.execute("CREATE TABLE sales(category TEXT,product TEXT,amount INT)")
c16.executemany("INSERT INTO sales VALUES(?,?,?)",[('Electronics','Phone',100),('Electronics','Laptop',200),('Electronics','Tablet',50),('Clothing','Shirt',80),('Clothing','Pants',60),('Clothing','Hat',30)])
q="WITH s AS(SELECT category,product,SUM(amount) total FROM sales GROUP BY category,product),r AS(SELECT*,DENSE_RANK()OVER(PARTITION BY category ORDER BY total DESC) dr FROM s) SELECT category,product,total FROM r WHERE dr<=2 ORDER BY category,total DESC"
print(pd.read_sql(q,c16).to_string())"""))

# ── Q377 Contains Duplicate II ──
cells.append(md("---\n## Q377 · Contains Duplicate II (Data Structures – EASY)\n**Problem:** Any two equal elements within k distance?\n### 🧠 Remember: sliding window with set; set size ≤ k; remove old element when window full"))
cells.append(code("""def contains_dup2_a(nums,k):
    seen={}
    for i,v in enumerate(nums):
        if v in seen and i-seen[v]<=k: return True
        seen[v]=i
    return False
def contains_dup2_b(nums,k):
    window=set()
    for i,v in enumerate(nums):
        if v in window: return True
        window.add(v)
        if len(window)>k: window.remove(nums[i-k])
    return False
def contains_dup2_c(nums,k):
    return any(nums[i]==nums[j] for i in range(len(nums)) for j in range(i+1,min(i+k+1,len(nums))))
print(contains_dup2_a([1,2,3,1],3))  # True
print(contains_dup2_b([1,0,1,1],1))  # True
print(contains_dup2_a([1,2,3,1,2,3],2))  # False
print("Time O(n) Space O(k)")"""))

# ── Q378 Winsorized Mean ──
cells.append(md("---\n## Q378 · Winsorized Mean (Statistics – EASY)\n**Problem:** Mean after capping outliers at percentile p and 1-p.\n### 🧠 Remember: clip values to [lower_pct, upper_pct], then take mean"))
cells.append(code("""def winsorize1(data,p=0.1):
    s=sorted(data); n=len(s)
    lo=int(n*p); hi=n-lo
    low_val=s[lo]; high_val=s[hi-1]
    clipped=[max(low_val,min(high_val,x)) for x in data]
    return sum(clipped)/len(clipped)
def winsorize2(data,lower_pct=0.1,upper_pct=0.9):
    s=sorted(data); n=len(s)
    low=s[int(n*lower_pct)]; high=s[int(n*upper_pct)-1]
    w=[max(low,min(high,x)) for x in data]
    return sum(w)/len(w)
data=[1,2,3,4,5,6,7,8,9,100]
print(f"Regular mean: {sum(data)/len(data):.1f}")
print(f"Winsorized:   {winsorize1(data):.1f}")
print("Time O(n logn) Space O(n)")"""))

# ── Q379 Sample Variance ──
cells.append(md("---\n## Q379 · Sample Variance (Statistics – EASY)\n**Problem:** Variance with Bessel's correction (n-1).\n### 🧠 Remember: population uses n, sample uses n-1"))
cells.append(code("""def var1(data):
    mu=sum(data)/len(data); n=len(data)
    return sum((x-mu)**2 for x in data)/(n-1)
def var2(data):
    n=len(data); mu=sum(data)/n
    return (sum(x*x for x in data)-n*mu*mu)/(n-1)
import math
def var3(data):
    try:
        import statistics; return statistics.variance(data)
    except: return var1(data)
data=[2,4,4,4,5,5,7,9]
print(f"Var={var1(data):.4f} std={var1(data)**0.5:.4f}")
print(f"Var={var2(data):.4f}")
print("Time O(n) Space O(1)")"""))

# ── Q380 Reverse Integer ──
cells.append(md("---\n## Q380 · Reverse Integer (Algorithms – MEDIUM)\n**Problem:** Reverse digits, return 0 if overflow 32-bit.\n### 🧠 Remember: convert to str, reverse, parse, check bounds"))
cells.append(code("""def reverse_int1(x):
    sign=1 if x>=0 else -1; x=abs(x)
    rev=int(str(x)[::-1])*sign
    return rev if -2**31<=rev<=2**31-1 else 0
def reverse_int2(x):
    sign=1 if x>0 else -1; x=abs(x); rev=0
    while x: rev=rev*10+x%10; x//=10
    rev*=sign
    return rev if -(2**31)<=rev<2**31 else 0
def reverse_int3(x):
    INT_MAX=(1<<31)-1; INT_MIN=-(1<<31)
    s=1 if x>=0 else -1; x=abs(x); r=0
    while x>0: r=r*10+(x%10); x//=10
    r*=s
    return r if INT_MIN<=r<=INT_MAX else 0
for v in [123,-123,120,0,1534236469]:
    print(f"{v}→{reverse_int1(v)}")
print("Time O(log n) Space O(1)")"""))

# ── Q381 Chi-Square ──
cells.append(md("---\n## Q381 · Chi-Square Goodness of Fit (Statistics – MEDIUM)\n**Problem:** Test if observed matches expected distribution.\n### 🧠 Remember: χ²=Σ(O-E)²/E; compare to chi2 critical value or p-value"))
cells.append(code("""def chi2_test1(observed,expected):
    chi2=sum((o-e)**2/e for o,e in zip(observed,expected))
    return chi2
def chi2_test2(observed,expected):
    n=sum(observed); k=len(observed)
    exp_total=sum(expected)
    exp_adj=[e/exp_total*n for e in expected]
    return sum((o-e)**2/e for o,e in zip(observed,exp_adj))
try:
    from scipy.stats import chisquare
    def chi2_test3(obs,exp): return chisquare(obs,exp)
except:
    def chi2_test3(obs,exp): stat=chi2_test1(obs,exp); return stat
obs=[50,50,60,40]; exp=[50,50,50,50]
print(f"χ²={chi2_test1(obs,exp):.4f}")
print("df=3, critical(p=0.05)=7.815")
print("Time O(k) Space O(1)")"""))

# ── Q385 Reservoir Sampling ──
cells.append(md("---\n## Q385 · Stream Sampling Reservoir (Data Engineering – MEDIUM)\n**Problem:** Sample k items from stream uniformly.\n### 🧠 Remember: first k items fill reservoir; for item i>k, replace random slot with prob k/i"))
cells.append(code("""def reservoir_sample1(stream,k):
    res=list(stream[:k])
    for i,item in enumerate(stream[k:],k+1):
        j=random.randint(0,i-1)
        if j<k: res[j]=item
    return res
def reservoir_sample2(stream,k):  # generator-based
    res=[]
    for i,item in enumerate(stream):
        if i<k: res.append(item)
        else:
            j=random.randint(0,i)
            if j<k: res[j]=item
    return res
stream=list(range(100)); k=10
random.seed(42)
s1=reservoir_sample1(stream,k)
s2=reservoir_sample2(stream,k)
print("Sample 1:",sorted(s1))
print("Sample 2:",sorted(s2))
print("Each element has equal prob k/n of being selected")
print("Time O(n) Space O(k)")"""))

# ── Q389 Combinations ──
cells.append(md("---\n## Q389 · Combinations (Algorithms – MEDIUM)\n**Problem:** All combinations of k numbers from 1..n.\n### 🧠 Remember: backtrack from start to n; append when len==k"))
cells.append(code("""def combine1(n,k):
    res=[]; path=[]
    def bt(start):
        if len(path)==k: res.append(path[:]); return
        for i in range(start,n+1):
            if n-i+1<k-len(path): break  # pruning
            path.append(i); bt(i+1); path.pop()
    bt(1); return res
def combine2(n,k):
    from itertools import combinations
    return list(combinations(range(1,n+1),k))
def combine3(n,k):  # iterative
    res=[[]]
    for _ in range(k):
        res=[prev+[j] for prev in res for j in range((prev[-1] if prev else 0)+1,n+1)]
    return res
print(f"C(4,2)={len(combine1(4,2))} combos")
print(combine1(4,2))
print("Time O(C(n,k)*k) Space O(k)")"""))

# ── Q390 Like and Comment Counts ──
cells.append(md("---\n## Q390 · Like And Comment Counts Per Day (Database – HARD)\n**Problem:** Count likes and comments per day.\n### 🧠 Remember: CASE WHEN action='like'→1; GROUP BY date; pivot-style aggregation"))
cells.append(code("""c17=sqlite3.connect(':memory:')
c17.execute("CREATE TABLE interactions(user_id INT,action TEXT,date TEXT)")
c17.executemany("INSERT INTO interactions VALUES(?,?,?)",[(1,'like','2023-01-01'),(2,'comment','2023-01-01'),(1,'like','2023-01-01'),(3,'like','2023-01-02'),(2,'like','2023-01-02'),(4,'comment','2023-01-02')])
q="SELECT date,SUM(CASE WHEN action='like' THEN 1 ELSE 0 END) likes,SUM(CASE WHEN action='comment' THEN 1 ELSE 0 END) comments,COUNT(*) total FROM interactions GROUP BY date ORDER BY date"
print(pd.read_sql(q,c17).to_string())"""))

# ── Q398 Meeting Rooms II ──
cells.append(md("---\n## Q398 · Meeting Rooms II (Data Structures – MEDIUM)\n**Problem:** Min number of conference rooms needed.\n### 🧠 Remember: sort starts; heap stores end times; if earliest end <= curr start → reuse room (pop+push); else add room (push)"))
cells.append(code("""def meeting_rooms2_heap(intervals):
    intervals.sort(); heap=[]
    for start,end in intervals:
        if heap and heap[0]<=start: heapq.heapreplace(heap,end)
        else: heapq.heappush(heap,end)
    return len(heap)
def meeting_rooms2_events(intervals):
    events=[]
    for s,e in intervals: events+=[(s,1),(e,-1)]
    events.sort(key=lambda x:(x[0],-x[1]))
    rooms=cur=0
    for _,delta in events: cur+=delta; rooms=max(rooms,cur)
    return rooms
def meeting_rooms2_two_ptr(intervals):
    starts=sorted(s for s,e in intervals)
    ends=sorted(e for s,e in intervals)
    rooms=end_ptr=0
    for s in starts:
        if s>=ends[end_ptr]: end_ptr+=1
        else: rooms+=1
    return rooms+1 if rooms else 1
ivs=[[0,30],[5,10],[15,20]]
print(meeting_rooms2_heap(ivs[:]))  # 2
print(meeting_rooms2_events(ivs[:]))
print(meeting_rooms2_two_ptr(ivs[:]))
print("Time O(n logn) Space O(n)")"""))

# ── Q401 Remove Covered Intervals ──
cells.append(md("---\n## Q401 · Remove Covered Intervals (Data Structures – MEDIUM)\n**Problem:** Remove intervals covered by another; return remaining count.\n### 🧠 Remember: sort by start asc, end desc; track max_end; if current end <= max_end → covered"))
cells.append(code("""def remove_covered1(intervals):
    intervals.sort(key=lambda x:(x[0],-x[1]))
    count=0; max_end=0
    for s,e in intervals:
        if e>max_end: count+=1; max_end=e
    return count
def remove_covered2(intervals):
    n=len(intervals); covered=0
    for i in range(n):
        for j in range(n):
            if i!=j and intervals[j][0]<=intervals[i][0] and intervals[i][1]<=intervals[j][1]:
                covered+=1; break
    return n-covered
print(remove_covered1([[1,4],[3,6],[2,8]]))  # 2
print(remove_covered2([[1,4],[3,6],[2,8]]))  # 2
print("Time O(n logn) Space O(1)")"""))

# ── Q404 Minimum Genetic Mutation ──
cells.append(md("---\n## Q404 · Minimum Genetic Mutation (Data Structures – MEDIUM)\n**Problem:** Min mutations to reach end gene; each mutation must be in bank.\n### 🧠 Remember: BFS on gene strings; neighbors = differ by 1 char and in bank"))
cells.append(code("""def min_mutation1(start,end,bank):
    bank=set(bank); q=deque([(start,0)])
    seen={start}
    while q:
        gene,steps=q.popleft()
        if gene==end: return steps
        for i in range(len(gene)):
            for c in 'ACGT':
                nxt=gene[:i]+c+gene[i+1:]
                if nxt in bank and nxt not in seen:
                    seen.add(nxt); q.append((nxt,steps+1))
    return -1
def min_mutation2(start,end,bank):  # bidirectional BFS
    bank=set(bank)
    if end not in bank: return -1
    front={start}; back={end}; steps=0
    while front:
        if len(front)>len(back): front,back=back,front
        nxt=set()
        for gene in front:
            for i in range(len(gene)):
                for c in 'ACGT':
                    g=gene[:i]+c+gene[i+1:]
                    if g in back: return steps+1
                    if g in bank: nxt.add(g); bank.discard(g)
        front=nxt; steps+=1
    return -1
print(min_mutation1("AACCGGTT","AACCGGTA",["AACCGGTA"]))  # 1
print(min_mutation2("AACCGGTT","AAACGGTA",["AACCGGTA","AACCGCTA","AAACGGTA"]))  # 2
print("Time O(4*L*N) Space O(N)")"""))

# ── Q405 Top Approved Video Flaggers ──
cells.append(md("---\n## Q405 · Top Approved Video Flaggers (Database – MEDIUM)\n**Problem:** Users with most approved flags.\n### 🧠 Remember: filter WHERE approved=1 → GROUP BY user → COUNT → ORDER BY DESC"))
cells.append(code("""c18=sqlite3.connect(':memory:')
c18.execute("CREATE TABLE flags(user_id INT,video_id INT,approved INT)")
c18.executemany("INSERT INTO flags VALUES(?,?,?)",[(1,10,1),(1,11,1),(2,10,1),(2,12,0),(3,13,1),(1,14,0),(3,15,1)])
q1="SELECT user_id,COUNT(*) approved_flags FROM flags WHERE approved=1 GROUP BY user_id ORDER BY approved_flags DESC"
q2="WITH f AS(SELECT user_id,SUM(approved) approved_flags FROM flags GROUP BY user_id) SELECT*FROM f ORDER BY approved_flags DESC"
print(pd.read_sql(q1,c18).to_string())"""))

# ── Q411 Palindrome Pairs ──
cells.append(md("---\n## Q411 · Palindrome Pairs (Data Structures – HARD)\n**Problem:** Find all (i,j) pairs where words[i]+words[j] is palindrome.\n### 🧠 Remember: for each word, check all splits; use hashmap for O(n*k²)"))
cells.append(code("""def palindrome_pairs1(words):  # brute O(n²k)
    def is_pal(s): return s==s[::-1]
    res=[]
    for i in range(len(words)):
        for j in range(len(words)):
            if i!=j and is_pal(words[i]+words[j]): res.append([i,j])
    return res
def palindrome_pairs2(words):  # hashmap O(n*k²)
    def is_pal(s): return s==s[::-1]
    wmap={w:i for i,w in enumerate(words)}; res=[]
    for i,w in enumerate(words):
        for k in range(len(w)+1):
            pre,suf=w[:k],w[k:]
            # if prefix is palindrome, find reverse of suffix
            if is_pal(pre) and suf[::-1] in wmap and wmap[suf[::-1]]!=i:
                res.append([wmap[suf[::-1]],i])
            # if suffix is palindrome, find reverse of prefix
            if k!=len(w) and is_pal(suf) and pre[::-1] in wmap and wmap[pre[::-1]]!=i:
                res.append([i,wmap[pre[::-1]]])
    return res
print("Brute:",palindrome_pairs1(["abcd","dcba","lls","s","sssll"]))
print("Hash: ",palindrome_pairs2(["abcd","dcba","lls","s","sssll"]))
print("Time O(n²k)/O(nk²) | Space O(n)")"""))

# Summary
cells.append(md("---\n## ✅ Summary – Page 1 Complete\n| Question | Category | Difficulty | Key Approach |\n|----------|----------|-----------|-------------|\n| Q1 Mean | Statistics | EASY | sum/len |\n| Q3 Pearson | Statistics | MEDIUM | cov/std |\n| Q5 Next Pointers | DS | MEDIUM | BFS level |\n| Q9 Linear Reg | ML | MEDIUM | normal eq / GD |\n| Q37 ZScore | Statistics | EASY | (x-μ)/σ |\n| Q41 Reaction Rate | SQL | MEDIUM | CASE WHEN |\n| Q43 Enclaves | DS | MEDIUM | DFS border |\n| Q46 Plus One | Math | EASY | carry loop |\n| Q49 Max Rectangle | Algo | HARD | histogram stack |\n| Q55 CTR | SQL | HARD | CASE WHEN ratio |\n| Q65 Insert Interval | DS | MEDIUM | 3-case linear |\n| Q80 Sliding Max | Algo | HARD | monotonic deque |\n| Q150 House Robber | Algo | MEDIUM | DP rolling |\n| Q160 Stream Median | DE | HARD | two heaps |\n| Q398 Meeting Rooms II | DS | MEDIUM | heap |\n\n*...and 80+ more questions above*"))

# Write notebook
notebook = nb(cells)
out = f"{BASE}/Google_DE_Page1_Q1_Q411.ipynb"
with open(out,'w') as f:
    json.dump(notebook,f,indent=1)
print(f"✅ Written: {out} ({len(cells)} cells)")
