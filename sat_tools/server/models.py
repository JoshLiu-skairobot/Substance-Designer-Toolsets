"""
Database Models

Defines SQLAlchemy models for the asset repository database.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class Asset:
    """Asset model representing an SBS/SBSAR source file."""
    id: str
    name: str
    description: str
    source_file: str  # Original filename (e.g., "material.sbs")
    source_file_url: Optional[str]  # URL to download the source file
    file_type: str  # 'sbs' or 'sbsar'
    storage_path: str  # Path to stored source file
    thumbnail_url: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: dict = field(default_factory=dict)
    # Processing status
    has_parameters: bool = False
    has_thumbnail: bool = False
    has_baked_textures: bool = False
    
    @classmethod
    def create(
        cls,
        name: str,
        source_file: str = "",
        source_file_url: Optional[str] = None,
        file_type: str = "sbs",
        description: str = "",
        storage_path: str = "",
        thumbnail_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
        has_parameters: bool = False,
        has_thumbnail: bool = False,
        has_baked_textures: bool = False
    ) -> 'Asset':
        """Create a new asset."""
        now = datetime.utcnow()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            source_file=source_file,
            source_file_url=source_file_url,
            file_type=file_type,
            storage_path=storage_path,
            thumbnail_url=thumbnail_url,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
            has_parameters=has_parameters,
            has_thumbnail=has_thumbnail,
            has_baked_textures=has_baked_textures
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sourceFile': self.source_file,
            'sourceFileUrl': self.source_file_url,
            'fileType': self.file_type,
            'storagePath': self.storage_path,
            'thumbnailUrl': self.thumbnail_url,
            'tags': self.tags,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata,
            'hasParameters': self.has_parameters,
            'hasThumbnail': self.has_thumbnail,
            'hasBakedTextures': self.has_baked_textures
        }


@dataclass
class Texture:
    """Texture model (belongs to an asset)."""
    id: str
    asset_id: str
    channel: str
    filename: str
    storage_path: str
    url: str
    format: str
    width: int
    height: int
    created_at: datetime
    
    @classmethod
    def create(
        cls,
        asset_id: str,
        channel: str,
        filename: str,
        storage_path: str,
        url: str,
        format: str = "png",
        width: int = 2048,
        height: int = 2048
    ) -> 'Texture':
        """Create a new texture."""
        return cls(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            channel=channel,
            filename=filename,
            storage_path=storage_path,
            url=url,
            format=format,
            width=width,
            height=height,
            created_at=datetime.utcnow()
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'assetId': self.asset_id,
            'channel': self.channel,
            'filename': self.filename,
            'url': self.url,
            'format': self.format,
            'resolution': {
                'width': self.width,
                'height': self.height
            }
        }


class Database:
    """
    Simple in-memory database with SQLite persistence.
    """
    
    def __init__(self, db_path: str = "assets.db"):
        """Initialize the database."""
        self.db_path = db_path
        self.assets: dict = {}
        self.textures: dict = {}
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create assets table with new columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                source_file TEXT,
                source_file_url TEXT,
                file_type TEXT DEFAULT 'sbs',
                storage_path TEXT,
                thumbnail_url TEXT,
                tags TEXT,
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT,
                has_parameters INTEGER DEFAULT 0,
                has_thumbnail INTEGER DEFAULT 0,
                has_baked_textures INTEGER DEFAULT 0
            )
        ''')
        
        # Add new columns if they don't exist (migration)
        try:
            cursor.execute('ALTER TABLE assets ADD COLUMN source_file_url TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE assets ADD COLUMN file_type TEXT DEFAULT "sbs"')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE assets ADD COLUMN has_parameters INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE assets ADD COLUMN has_thumbnail INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE assets ADD COLUMN has_baked_textures INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        # Create textures table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS textures (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                channel TEXT,
                filename TEXT,
                storage_path TEXT,
                url TEXT,
                format TEXT,
                width INTEGER,
                height INTEGER,
                created_at TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load data from SQLite."""
        import sqlite3
        import json
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Load assets
        cursor.execute('SELECT * FROM assets')
        for row in cursor.fetchall():
            asset = Asset(
                id=row['id'],
                name=row['name'],
                description=row['description'] or '',
                source_file=row['source_file'] or '',
                source_file_url=row['source_file_url'] if 'source_file_url' in row.keys() else None,
                file_type=row['file_type'] if 'file_type' in row.keys() else 'sbs',
                storage_path=row['storage_path'] or '',
                thumbnail_url=row['thumbnail_url'],
                tags=json.loads(row['tags']) if row['tags'] else [],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow(),
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                has_parameters=bool(row['has_parameters']) if 'has_parameters' in row.keys() else False,
                has_thumbnail=bool(row['has_thumbnail']) if 'has_thumbnail' in row.keys() else False,
                has_baked_textures=bool(row['has_baked_textures']) if 'has_baked_textures' in row.keys() else False
            )
            self.assets[asset.id] = asset
        
        # Load textures
        cursor.execute('SELECT * FROM textures')
        for row in cursor.fetchall():
            texture = Texture(
                id=row['id'],
                asset_id=row['asset_id'],
                channel=row['channel'] or '',
                filename=row['filename'] or '',
                storage_path=row['storage_path'] or '',
                url=row['url'] or '',
                format=row['format'] or 'png',
                width=row['width'] or 2048,
                height=row['height'] or 2048,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            self.textures[texture.id] = texture
        
        conn.close()
    
    def save_asset(self, asset: Asset):
        """Save an asset to the database."""
        import sqlite3
        import json
        
        self.assets[asset.id] = asset
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO assets 
            (id, name, description, source_file, source_file_url, file_type,
             storage_path, thumbnail_url, tags, created_at, updated_at, metadata,
             has_parameters, has_thumbnail, has_baked_textures)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            asset.id,
            asset.name,
            asset.description,
            asset.source_file,
            asset.source_file_url,
            asset.file_type,
            asset.storage_path,
            asset.thumbnail_url,
            json.dumps(asset.tags),
            asset.created_at.isoformat() if asset.created_at else None,
            asset.updated_at.isoformat() if asset.updated_at else None,
            json.dumps(asset.metadata),
            1 if asset.has_parameters else 0,
            1 if asset.has_thumbnail else 0,
            1 if asset.has_baked_textures else 0
        ))
        
        conn.commit()
        conn.close()
    
    def save_texture(self, texture: Texture):
        """Save a texture to the database."""
        import sqlite3
        
        self.textures[texture.id] = texture
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO textures 
            (id, asset_id, channel, filename, storage_path, url, 
             format, width, height, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            texture.id,
            texture.asset_id,
            texture.channel,
            texture.filename,
            texture.storage_path,
            texture.url,
            texture.format,
            texture.width,
            texture.height,
            texture.created_at.isoformat() if texture.created_at else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Get an asset by ID."""
        return self.assets.get(asset_id)
    
    def get_assets(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> tuple:
        """Get paginated list of assets."""
        assets = list(self.assets.values())
        
        # Filter by search
        if search:
            search_lower = search.lower()
            assets = [a for a in assets if 
                      search_lower in a.name.lower() or 
                      search_lower in a.description.lower() or
                      search_lower in a.source_file.lower()]
        
        # Filter by tags
        if tags:
            assets = [a for a in assets if 
                      any(t in a.tags for t in tags)]
        
        # Sort by created_at descending
        assets.sort(key=lambda a: a.created_at, reverse=True)
        
        # Paginate
        total = len(assets)
        start = (page - 1) * page_size
        end = start + page_size
        
        return assets[start:end], total
    
    def get_textures_for_asset(self, asset_id: str) -> List[Texture]:
        """Get all textures for an asset."""
        return [t for t in self.textures.values() if t.asset_id == asset_id]
    
    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset and its textures."""
        import sqlite3
        
        if asset_id not in self.assets:
            return False
        
        # Delete from memory
        del self.assets[asset_id]
        texture_ids = [t.id for t in self.textures.values() if t.asset_id == asset_id]
        for tid in texture_ids:
            del self.textures[tid]
        
        # Delete from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM textures WHERE asset_id = ?', (asset_id,))
        cursor.execute('DELETE FROM assets WHERE id = ?', (asset_id,))
        conn.commit()
        conn.close()
        
        return True
