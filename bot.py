import discord
from discord.ext import commands, tasks
from discord_slash import SlashCommand
client = commands.Bot(command_prefix="%")
slash = SlashCommand(client, sync_commands=True)
import mysql.connector
from datetime import date, timedelta, datetime, timezone
from discord.ext.commands import UserNotFound
from table2ascii import table2ascii as t2a, PresetStyle, Alignment
import re

config = {
'user': '',
'password': '',
'host': '',
'port': '3306',
'database': '',
'raise_on_warnings': True,}

mydb = mysql.connector.connect(**config)    
mycursor = mydb.cursor()

client.remove_command('help')

@client.event
async def on_ready():
    activity = discord.Game(name="For help | %h", type=3)
    await client.change_presence(status=discord.Status.idle, activity=activity)
    print("Bot is alive and well!!")
    await client.wait_until_ready()


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, UserNotFound):
        await ctx.send("Please mention a user instead of whatever you sent") 

@client.command(aliases=['c'])
async def clear(ctx):
        mycursor.execute("DELETE FROM vacation")
        await ctx.send("All data in the table has been cleared succesfully!")

@client.command(aliases=['tl'])
async def totallist(ctx):
        mycursor.execute("SELECT CASE WHEN EXISTS(SELECT 1 FROM vacation) THEN 0 ELSE 1 END AS IsEmpty;")
        result = mycursor.fetchall()
        res = "".join(map(str, result))
        if res == '(0,)':
            today = date.today()
            d1 = today.strftime("%d/%m/%Y")
            mycursor.execute("SELECT * FROM vacation WHERE begin <= '"+d1+"'")
            tableview = mycursor.fetchall()
            tableview = [list(i) for i  in tableview]
            for x, lst in enumerate(tableview):
                if len(lst[-1]) > 74:
                    rem = lst[-1][74::]
                    lst[-1] = lst[-1][:74]
                    tableview.insert(x+1, ["", "", "", "", rem])

            output = t2a(
                    header=["Username", "Start Date", "End Date", "Duration", "Reason"],
                    body=tableview,
                    first_col_heading=True,
                    alignments=[Alignment.LEFT] * 5)
            await ctx.send(f"```\n{output}\n```")
        else:
            await ctx.send("```\nEverybody is Available Today\n```")

@client.command(aliases=['ul'])
async def userlist(ctx):
        mycursor.execute("SELECT CASE WHEN EXISTS(SELECT 1 FROM vacation) THEN 0 ELSE 1 END AS IsEmpty;")
        result = mycursor.fetchall()
        res = "".join(map(str, result))
        if res == '(0,)':
            mycursor.execute("SELECT username FROM vacation")
            tableview = mycursor.fetchall()
            tableview = [list(i) for i  in tableview]
            output = t2a(
                    header=["Username"],
                    body=tableview,
                    first_col_heading=True)
            await ctx.send(f"```\n{output}\n```")
        else:
            await ctx.send("```\nEverybody is Available Today\n```")

addoption = [
    {
        "name": "member",
        "description": "The Staff member going on Vacation",
        "required": True,
        "type":6
        
    },
    {
        "name": "duration",
        "description": "The length of your Vacation",
        "required": True,
        "type":4

    },
    {
        "name": "reason",
        "description": "The reason of your Vacation",
        "required": True,
        "type":3
    }
]

@slash.slash(name="add", description="Add a Staff member to the vacation list", options=addoption)
@client.command(aliases=["a"])
async def tableadd(ctx, member: discord.User, duration, *,reason):
    if "<:" in reason and ">" in reason:
        reason = re.sub('<.*?>', '', reason)
    string_unicode = member.name
    string_encode = string_unicode.encode("ascii", "ignore")
    name = string_encode.decode()
    sqlFormula = "INSERT INTO vacation (username, begin, end, duration, reason) VALUES (%s, %s, %s, %s, %s)"
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    newtoday = today + timedelta(int(duration))
    d2 = newtoday.strftime("%d/%m/%Y")
    person = ( name, d1, d2, duration, reason)
    mycursor.execute(sqlFormula, person)
    mydb.commit()
    await ctx.send("You have succesfully added "+name+" to the Vacation List!")

@client.command(aliases=["an"])
async def addnext(ctx, member: discord.User, duration1, duration2, *,reason):
    string_unicode = member.name
    string_encode = string_unicode.encode("ascii", "ignore")
    name = string_encode.decode()
    sqlFormula = "INSERT INTO vacation (username, begin, end, duration, reason) VALUES (%s, %s, %s, %s, %s)"
    today = date.today() + timedelta(int(duration1))
    d1 = today.strftime("%d/%m/%Y")
    newtoday = today + timedelta(int(duration2))
    d2 = newtoday.strftime("%d/%m/%Y")
    person = ( name, d1, d2, duration2, reason)
    mycursor.execute(sqlFormula, person)
    mydb.commit()
    await ctx.send(name+" will appear on the Vacation List "+duration1+" days from now!")

editoption = [
    {
        "name": "member",
        "description": "The Staff member whose duration you want to edit",
        "required": True,
        "type":6
        
    },
    {
        "name": "duration",
        "description": "The length of your Vacation",
        "required": True,
        "type":4

    }
]
@slash.slash(name="edit", description="Edit the vacation duration of a staff member", options=editoption)
@client.command(aliases=['e'])
async def edit(ctx, member: discord.User, duration):
    string_unicode = member.name
    string_encode = string_unicode.encode("ascii", "ignore")
    name = string_encode.decode()
    mycursor.execute("SELECT begin FROM vacation WHERE username = '"+name+"'")
    value = mycursor.fetchall()
    for row in value:
        rows = "".join(map(str, row))
        today = datetime.strptime(rows, '%d/%m/%Y')
        newtoday = today + timedelta(int(duration))
        d2 = newtoday.strftime("%d/%m/%Y")
    sqld = "UPDATE vacation SET duration = '"+duration+"' WHERE username = '"+name+"'"
    sqlt = "UPDATE vacation SET end = '"+d2+"' WHERE username = '"+name+"'"
    mycursor.execute(sqld)
    mycursor.execute(sqlt)
    mydb.commit()
    await ctx.send("Succesfully updated "+name+"'s Vacation time to "+duration+" days!")

deloption = [
    {
        "name": "member",
        "description": "The Staff member you want to remove from the list",
        "required": True,
        "type":6
        
    }
]
@slash.slash(name="remove", description="Remove a staff member from vacation", options=deloption)
@client.command(aliases=['r'])
async def remove(ctx, member: discord.User):
    string_unicode = member.name
    string_encode = string_unicode.encode("ascii", "ignore")
    name = string_encode.decode()
    sql = 'DELETE FROM vacation WHERE username = "'+name+'"'
    mycursor.execute(sql)
    mydb.commit()
    await ctx.send("Deleted "+name+" from Vacations!")

@tasks.loop(minutes=10, count=None)
async def del_field():
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    sql = "DELETE FROM vacation WHERE end = '"+d1+"'"
    mycursor.execute(sql)
    mydb.commit()

@tasks.loop(minutes=1, count=None)
async def reset_month():
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    d2 = d1[:2]
    if d2 == "01":
        sql = "UPDATE vacation SET begin = '"+d1+"'"
        mycursor.execute(sql)
        mydb.commit()

@client.command(aliases=['date'])
async def datecheck(ctx):
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    print(d1)

@tasks.loop(minutes=1, count=None)
async def dailytime():
        current = str(datetime.now())
        df = current[-15:]
        df2 = df[:5]
        compare = '09:00'
        if df2 == compare:
            channellist = [
            '657999029141110805', 
            '779636221206724642',
            '796284442594377748'
            ]
            for channel_id in channellist:
                channel = client.get_channel(int(channel_id))

                mycursor.execute("SELECT CASE WHEN EXISTS(SELECT 1 FROM vacation) THEN 0 ELSE 1 END AS IsEmpty;")
                result = mycursor.fetchall()
                res = "".join(map(str, result))
                if res == '(0,)':
                    today = date.today()
                    d1 = today.strftime("%d/%m/%Y")
                    mycursor.execute("SELECT * FROM vacation WHERE begin <= '"+d1+"'")
                    tableview = mycursor.fetchall()
                    tableview = [list(i) for i  in tableview]
                    for x, lst in enumerate(tableview):
                        if len(lst[-1]) > 74:
                            rem = lst[-1][74::]
                            lst[-1] = lst[-1][:74]
                            tableview.insert(x+1, ["", "", "", "", rem])

                    output = t2a(
                            header=["Username", "Start Date", "End Date", "Duration", "Reason"],
                            body=tableview,
                            first_col_heading=True,
                            alignments=[Alignment.LEFT] * 5)
                    await channel.send(f"```\n{output}\n```")
                else:
                    await channel.send("```\nEverybody is Available Today\n```")
        

@client.command(aliases=['h'])
async def help(ctx):
    out = [ 
    ["1", "%a @user <duration> <reason>", "To add user to Vacation list"],
    ["2", "%an @user <days after today> <duration> <reason>", "To add user to Vacation list after a specific number of days"],
    ["3", "%r @user", "To remove user from Vacation list"],
    ["4", "%c", "To clear all entries in the table"],
    ["5", "%e @user <duration>", "Edits the duration of the user's vacation"],
    ["6", "%tl", "Shows all information of the Users on Vacation"],
    ["7", "%ul", "Shows users that are on Vacation"],
    ["8", "%h", "Help command"]]
    output = t2a(
        header = ["#", "Command", "Function"],
        body = out,
        first_col_heading=True,
        alignments=[Alignment.LEFT]*3
    )
    await ctx.send(f"```\n{output}\n```")


del_field.start()
dailytime.start()
reset_month.start()
client.run('')