import json

from neo4j import GraphDatabase

# Define Neo4j connection
host = 'neo4j+s://375d00f3.databases.neo4j.io:7687'
username = 'neo4j'
password = 'n0qpoWvToMdCgoj9n9U5cUlItVyO_PbpCF0b_a1GQbE'

def find(name):
    cypher_query_template = """
        MATCH (p:Entity {text: $name })-[:DATE_OF_BIRTH]->(dob:Entity),
        (p:Entity {text: $name})-[:DATE_OF_DEATH]->(dod:Entity),
        (p:Entity {text: $name})-[:PLACE_OF_BIRTH]->(pob:Entity),
        (p:Entity {text: $name})-[:PLACE_OF_DEATH]->(pod:Entity),
        (p:Entity {text: $name})-[:POSITION_HELD]->(ph:Entity),
        (p:Entity {text: $name})-[:EDUCATED_AT]->(ea:Entity),
        (p:Entity {text: $name})-[:SPOUSE]->(s:Entity),
        (p:Entity {text: $name})-[:CHILD]->(c:Entity),
        (p:Entity {text: $name})-[:MILITARY_RANK]->(mr:Entity),
        (p:Entity {text: $name})-[:MEMBER_OF_POLITICAL_PARTY]->(mopp:Entity)
        RETURN p.text AS Name, dob.text AS Date_of_Birth, dod.text AS Date_of_Death, pob.text AS Place_of_Birth, pod.text AS Place_of_Death, ph.text AS Position_Held, ea.text AS Educated_At, s.text AS Spouse, c.text AS Child, 
        mr.text AS Military_Rank, mopp.text AS Member_of_Political_Party
    """
    driver = GraphDatabase.driver(f"{host}", auth=(username, password))
    with driver.session() as session:
        result = session.run(cypher_query_template, name=name)
        records = [record.data() for record in result]
        return records