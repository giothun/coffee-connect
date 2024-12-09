

def blossom_algorithm(edges):
    if not edges:
        return []
    nedge = len(edges)
    nvertex = 0
    for (i, j, w) in edges:
        if i >= nvertex:
            nvertex = i + 1
        if j >= nvertex:
            nvertex = j + 1
    maxweight = max(0, max([wt for (i, j, wt) in edges]))
    endpoint = [edges[p // 2][p % 2] for p in range(2 * nedge)]
    neighbend = [[] for i in range(nvertex)]
    for k in range(len(edges)):
        (i, j, w) = edges[k]
        neighbend[i].append(2 * k + 1)
        neighbend[j].append(2 * k)
    mate = nvertex * [-1]
    label = (2 * nvertex) * [0]
    labelend = (2 * nvertex) * [-1]
    inblossom = list(range(nvertex))
    blossomparent = (2 * nvertex) * [-1]
    blossomchilds = (2 * nvertex) * [None]
    blossombase = list(range(nvertex)) + nvertex * [-1]
    blossomendps = (2 * nvertex) * [None]
    bestedge = (2 * nvertex) * [-1]
    blossombestedges = (2 * nvertex) * [None]
    unusedblossoms = list(range(nvertex, 2 * nvertex))
    dualvar = nvertex * [maxweight] + nvertex * [0]
    allowedge = nedge * [False]
    queue = []

    def slack(k):
        (i, j, wt) = edges[k]
        return dualvar[i] + dualvar[j] - 2 * wt

    def blossom_leaves(b):
        if b < nvertex:
            yield b
        else:
            for t in blossomchilds[b]:
                if t < nvertex:
                    yield t
                else:
                    for v in blossom_leaves(t):
                        yield v

    def assign_label(w, t, p):
        b = inblossom[w]
        label[w] = label[b] = t
        labelend[w] = labelend[b] = p
        bestedge[w] = bestedge[b] = -1
        if t == 1:
            queue.extend(blossom_leaves(b))
        elif t == 2:
            base = blossombase[b]
            assign_label(endpoint[mate[base]], 1, mate[base] ^ 1)

    def scan_blossom(v, w):
        path = []
        base = -1
        while v != -1 or w != -1:
            b = inblossom[v]
            if label[b] & 4:
                base = blossombase[b]
                break
            path.append(b)
            label[b] = 5
            if labelend[b] == -1:
                v = -1
            else:
                v = endpoint[labelend[b]]
                b = inblossom[v]
                v = endpoint[labelend[b]]
            if w != -1:
                v, w = w, v
        for b in path:
            label[b] = 1
        return base

    def add_blossom(base, k):
        (v, w, wt) = edges[k]
        bb = inblossom[base]
        bv = inblossom[v]
        bw = inblossom[w]
        b = unusedblossoms.pop()
        blossombase[b] = base
        blossomparent[b] = -1
        blossomparent[bb] = b
        blossomchilds[b] = path = []
        blossomendps[b] = endps = []
        while bv != bb:
            blossomparent[bv] = b
            path.append(bv)
            endps.append(labelend[bv])
            v = endpoint[labelend[bv]]
            bv = inblossom[v]
        path.append(bb)
        path.reverse()
        endps.reverse()
        endps.append(2 * k)
        while bw != bb:
            blossomparent[bw] = b
            path.append(bw)
            endps.append(labelend[bw] ^ 1)
            w = endpoint[labelend[bw]]
            bw = inblossom[w]
        label[b] = 1
        labelend[b] = labelend[bb]
        dualvar[b] = 0
        for v in blossom_leaves(b):
            if label[inblossom[v]] == 2:
                queue.append(v)
            inblossom[v] = b
        bestedgeto = (2 * nvertex) * [-1]
        for bv in path:
            if blossombestedges[bv] is None:
                nblists = [[p // 2 for p in neighbend[v]]
                           for v in blossom_leaves(bv)]
            else:
                nblists = [blossombestedges[bv]]
            for nblist in nblists:
                for k in nblist:
                    (i, j, wt) = edges[k]
                    if inblossom[j] == b:
                        i, j = j, i
                    bj = inblossom[j]
                    if (bj != b and label[bj] == 1 and
                            (bestedgeto[bj] == -1 or
                             slack(k) < slack(bestedgeto[bj]))):
                        bestedgeto[bj] = k
            blossombestedges[bv] = None
            bestedge[bv] = -1
        blossombestedges[b] = [k for k in bestedgeto if k != -1]
        bestedge[b] = -1
        for k in blossombestedges[b]:
            if bestedge[b] == -1 or slack(k) < slack(bestedge[b]):
                bestedge[b] = k

    def expand_blossom(b, endstage):
        for s in blossomchilds[b]:
            blossomparent[s] = -1
            if s < nvertex:
                inblossom[s] = s
            elif endstage and dualvar[s] == 0:
                expand_blossom(s, endstage)
            else:
                for v in blossom_leaves(s):
                    inblossom[v] = s
        if (not endstage) and label[b] == 2:
            entrychild = inblossom[endpoint[labelend[b] ^ 1]]
            j = blossomchilds[b].index(entrychild)
            if j & 1:
                j -= len(blossomchilds[b])
                jstep = 1
                endptrick = 0
            else:
                jstep = -1
                endptrick = 1
            p = labelend[b]
            while j != 0:
                label[endpoint[p ^ 1]] = 0
                label[endpoint[blossomendps[b][j - endptrick] ^ endptrick ^ 1]] = 0
                assign_label(endpoint[p ^ 1], 2, p)
                allowedge[blossomendps[b][j - endptrick] // 2] = True
                j += jstep
                p = blossomendps[b][j - endptrick] ^ endptrick
                allowedge[p // 2] = True
                j += jstep
            bv = blossomchilds[b][j]
            label[endpoint[p ^ 1]] = label[bv] = 2
            labelend[endpoint[p ^ 1]] = labelend[bv] = p
            bestedge[bv] = -1
            j += jstep
            while blossomchilds[b][j] != entrychild:
                bv = blossomchilds[b][j]
                if label[bv] == 1:
                    j += jstep
                    continue
                for v in blossom_leaves(bv):
                    if label[v] != 0:
                        break
                if label[v] != 0:
                    label[v] = 0
                    label[endpoint[mate[blossombase[bv]]]] = 0
                    assign_label(v, 2, labelend[v])
                j += jstep
        label[b] = labelend[b] = -1
        blossomchilds[b] = blossomendps[b] = None
        blossombase[b] = -1
        blossombestedges[b] = None
        bestedge[b] = -1
        unusedblossoms.append(b)

    def augment_blossom(b, v):
        t = v
        while blossomparent[t] != b:
            t = blossomparent[t]
        if t >= nvertex:
            augment_blossom(t, v)
        i = j = blossomchilds[b].index(t)
        if i & 1:
            j -= len(blossomchilds[b])
            jstep = 1
            endptrick = 0
        else:
            jstep = -1
            endptrick = 1
        while j != 0:
            j += jstep
            t = blossomchilds[b][j]
            p = blossomendps[b][j - endptrick] ^ endptrick
            if t >= nvertex:
                augment_blossom(t, endpoint[p])
            j += jstep
            t = blossomchilds[b][j]
            if t >= nvertex:
                augment_blossom(t, endpoint[p ^ 1])
            mate[endpoint[p]] = p ^ 1
            mate[endpoint[p ^ 1]] = p
        blossomchilds[b] = blossomchilds[b][i:] + blossomchilds[b][:i]
        blossomendps[b] = blossomendps[b][i:] + blossomendps[b][:i]
        blossombase[b] = blossombase[blossomchilds[b][0]]

    def augment_matching(k):
        (v, w, wt) = edges[k]
        for (s, p) in ((v, 2 * k + 1), (w, 2 * k)):
            while 1:
                bs = inblossom[s]
                if bs >= nvertex:
                    augment_blossom(bs, s)
                mate[s] = p
                if labelend[bs] == -1:
                    break
                t = endpoint[labelend[bs]]
                bt = inblossom[t]
                s = endpoint[labelend[bt]]
                j = endpoint[labelend[bt] ^ 1]
                if bt >= nvertex:
                    augment_blossom(bt, j)
                mate[j] = labelend[bt]
                p = labelend[bt] ^ 1

    for t in range(nvertex):
        label[:] = (2 * nvertex) * [0]
        bestedge[:] = (2 * nvertex) * [-1]
        blossombestedges[nvertex:] = nvertex * [None]
        allowedge[:] = nedge * [False]
        queue[:] = []
        for v in range(nvertex):
            if mate[v] == -1 and label[inblossom[v]] == 0:
                assign_label(v, 1, -1)

        augmented = 0
        while 1:
            while queue and not augmented:
                v = queue.pop()
                for p in neighbend[v]:
                    k = p // 2
                    w = endpoint[p]
                    if inblossom[v] == inblossom[w]:
                        continue
                    if not allowedge[k]:
                        kslack = slack(k)
                        if kslack <= 0:
                            allowedge[k] = True
                    if allowedge[k]:
                        if label[inblossom[w]] == 0:
                            assign_label(w, 2, p ^ 1)
                        elif label[inblossom[w]] == 1:
                            base = scan_blossom(v, w)
                            if base >= 0:
                                add_blossom(base, k)
                            else:
                                augment_matching(k)
                                augmented = 1
                                break
                        elif label[w] == 0:
                            label[w] = 2
                            labelend[w] = p ^ 1
                    elif label[inblossom[w]] == 1:
                        b = inblossom[v]
                        if bestedge[b] == -1 or kslack < slack(bestedge[b]):
                            bestedge[b] = k
                    elif label[w] == 0:
                        if bestedge[w] == -1 or kslack < slack(bestedge[w]):
                            bestedge[w] = k
            if augmented:
                break
            deltatype = -1
            delta = deltaedge = deltablossom = None

            for v in range(nvertex):
                if label[inblossom[v]] == 0 and bestedge[v] != -1:
                    d = slack(bestedge[v])
                    if deltatype == -1 or d < delta:
                        delta = d
                        deltatype = 2
                        deltaedge = bestedge[v]

            for b in range(2 * nvertex):
                if (blossomparent[b] == -1 and label[b] == 1 and
                        bestedge[b] != -1):
                    kslack = slack(bestedge[b])
                    if isinstance(kslack, int):
                        d = kslack // 2
                    else:
                        d = kslack / 2
                    if deltatype == -1 or d < delta:
                        delta = d
                        deltatype = 3
                        deltaedge = bestedge[b]

            for b in range(nvertex, 2 * nvertex):
                if (blossombase[b] >= 0 and blossomparent[b] == -1 and
                        label[b] == 2 and
                        (deltatype == -1 or dualvar[b] < delta)):
                    delta = dualvar[b]
                    deltatype = 4
                    deltablossom = b

            if deltatype == -1:
                deltatype = 1
                delta = max(0, min(dualvar[:nvertex]))

            for v in range(nvertex):
                if label[inblossom[v]] == 1:
                    dualvar[v] -= delta
                elif label[inblossom[v]] == 2:
                    dualvar[v] += delta
            for b in range(nvertex, 2 * nvertex):
                if blossombase[b] >= 0 and blossomparent[b] == -1:
                    if label[b] == 1:
                        dualvar[b] += delta
                    elif label[b] == 2:
                        dualvar[b] -= delta
            if deltatype == 1:
                break
            elif deltatype == 2:
                allowedge[deltaedge] = True
                (i, j, wt) = edges[deltaedge]
                if label[inblossom[i]] == 0:
                    i, j = j, i
                queue.append(i)
            elif deltatype == 3:
                allowedge[deltaedge] = True
                (i, j, wt) = edges[deltaedge]
                queue.append(i)
            elif deltatype == 4:
                expand_blossom(deltablossom, False)
        if not augmented:
            break
        for b in range(nvertex, 2 * nvertex):
            if (blossomparent[b] == -1 and blossombase[b] >= 0 and
                    label[b] == 1 and dualvar[b] == 0):
                expand_blossom(b, True)

    for v in range(nvertex):
        if mate[v] >= 0:
            mate[v] = endpoint[mate[v]]

    pairs = []
    used = [0] * nvertex

    for i, mt in enumerate(mate):
        if mt != -1 and not used[mt] and not used[i]:
            used[mt] = 1
            used[i] = 1
            pairs.append((i, mt))

    return pairs, sum([w for i, j, w in edges if (i, j) in pairs])
