# crowd-vpn-server

A minimum viable control-plane prototype for a crowdsourced VPN platform.

## Overview

This project implements a lightweight central directory server for OpenWrt-based WireGuard nodes.  
It is designed as the second-stage prototype of the system, moving from manual tunnel configuration to an initial automated control plane.

The server is built with:

- Python
- Flask
- SQLite

## Current Features

- Node registration
- Heartbeat reporting
- Online/offline status maintenance
- Basic node matching
- Minimal credit update logic

## API Endpoints

- `POST /api/register`  
  Register a node and store its basic information.

- `POST /api/heartbeat`  
  Update node heartbeat, public endpoint, and available bandwidth.

- `GET /api/nodes`  
  Query all nodes and their current status.

- `POST /api/match`  
  Return one available online node for a requester and update credits.

## Database

The prototype uses a local SQLite database:

- `directory.db`

The `nodes` table stores:

- node identity
- WireGuard public key
- tunnel IP
- reported public IP and port
- available bandwidth
- credit
- online/offline status
- last heartbeat time

## Run

Initialize the database:

```bash
python init_db.py
