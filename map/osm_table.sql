
create table sgp_osm_nodes (
osm_id bigint,
lat numeric not null,
lon numeric not null,
primary key (osm_id));

create table sgp_osm_ways (
osm_id bigint,
idx int,
ref_id bigint,
primary key (osm_id,idx));

create table sgp_osm_relations (
osm_id bigint,
idx int,
member_id bigint,
member_type varchar(16),
member_role varchar(16),
primary key (osm_id,idx));

create table sgp_osm_tags (
osm_id bigint,
source int,
key varchar(128),
value varchar(256),
primary key (osm_id,key));

copy sgp_osm_nodes from '/home/share/osm.nodes.csv'
with csv header


