from .basicrace import basicrace

async def setup(bot):
    await bot.add_cog(basicrace(bot))