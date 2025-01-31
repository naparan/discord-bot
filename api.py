import asyncio
async def req(ctx,url,headers,session):
    try:
        async with session.get(url,headers=headers) as res:
            if res.status == 429:
                retry = float(res.headers.get("Retry-After","1"))
                await ctx.send(f"リクエスト過多 {retry}秒後に再試行します")
                await asyncio.sleep(retry)
                return await req(ctx,url,headers,session)
            elif res.status == 200:
                return await res.json()
            else:
                await ctx.send("イベント情報の取得に失敗しました")
                return None
    except Exception as e:
        print(f"error in def req():\n{e}")
        
async def op(ctx,url,headers,session,OP,code):
    try:
        if OP not in ['get', 'post', 'put', 'delete', 'patch']:
            print("無効なhttpメソッドが指定されました")
            return False
        async with getattr(session, OP)(url,headers = headers) as res:
            if res.status == 429:
                retry = float(res.headers.get("Retry-After","1"))
                await ctx.send(f"リクエスト過多{retry}秒後に再試行します")
                await asyncio.sleep(retry)
                return await op(ctx,url,headers,session,OP,code)
            elif res.status == code or res.status == 200:
                return True
            else:
                await ctx.send(f"リクエストに失敗しました　ステータスコード：{res.status}")
                print(f"failed in def op():\ncode{res.status}")
                return False
    except Exception as e:
        print(f"error in def op():\n{e}")
        
async def op_create(ctx,url,headers,session,event_data):
    try:
        async with session.post(url,headers=headers,json=event_data) as res:
            if res.status == 429:
                retry = float(res.headers.get("Retry-After","1"))
                await ctx.send(f"リクエスト過多{retry}秒後に再試行します")
                await asyncio.sleep(retry)
                return await op_create(ctx,url,headers,session,event_data)
            elif res.status == 201 or 200:
                return True
            else:
                await ctx.send(f"リクエストに失敗しました　ステータスコード：{res.status}")
                print(f"failed in def create():\n{res.status}")
                return False
    except Exception as e:
        print(f"error in def create() in api.py:\n{e}")