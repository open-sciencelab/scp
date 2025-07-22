from scp.lab.client import SciLabClient
def example():
    # Create client
    try:
        client = SciLabClient("http://127.0.0.1:8081")
        servers = client.list_servers()
        print(servers)

        tools = client.list_tools()
        print(tools)

        # Call a tool
        result  =  client.call_tool("git-demo.predict_signalpeptide",
                                { "protein": "MGQPGNGSAFLLAPNGSHAPDHDVTQERDEVWVVGMGIVMSLIVLAIVFGNVLVITAIAKFERLQTVTNY FITSLACADLVMGLAVVPFGAAHILMKMWTFGNFWCEFWTSIDVLCVTASIETLCVIAVDRYFAITSPFK YQSLLTKNKARVIILMVWIVSGLTSFLPIQMHWYRATHQEAINCYANETCCDFFTNQAYAIASSIVSFYV PLVIMVFVYSRVFQEAKRQLQKIDKSEGRFHVQNLSQVEQDGRTGHGLRRSSKFCLKEHKALKTLGIIMG TFTLCWLPFFIVNIVHVIQDNLIRKEVYILLNWIGYVNSGFNPLIYCRSPDFRIAFQELLCLRRSSLKAY GNGYSSNGNTGEQSGYHVEQEKENKLLCEDLPGTEDFVGHQGTVPSDNIDSQGRNCSTNDSLL"})
        print(result)
    
    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    example()
