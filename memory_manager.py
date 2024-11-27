from datetime import datetime
from sqlalchemy import desc
from models import Memory, db
import json

class MemoryManager:
    def __init__(self):
        self.decay_factor = 0.1  # Memory confidence decay factor
        
    def store_memory(self, memory_type: str, key: str, value: dict, confidence: float = 1.0):
        """Store a new memory or update existing one"""
        from flask import current_app
        
        try:
            with current_app.app_context():
                # Validate input
                if not isinstance(value, dict):
                    raise ValueError("Memory value must be a dictionary")
                    
                memory = Memory.query.filter_by(memory_type=memory_type, key=key).first()
                if memory:
                    # Update existing memory
                    memory.value = value
                    memory.confidence = min(1.0, max(0.1, confidence))  # Ensure confidence is between 0.1 and 1.0
                    memory.updated_at = datetime.utcnow()
                else:
                    # Create new memory
                    memory = Memory(
                        memory_type=memory_type,
                        key=key,
                        value=value,
                        confidence=min(1.0, max(0.1, confidence))
                    )
                    db.session.add(memory)
                
                db.session.commit()
                return True
        except ValueError as e:
            print(f"Validation error while storing memory: {str(e)}")
            return False
        except Exception as e:
            if 'current_app' in locals():
                db.session.rollback()
            print(f"Error storing memory: {str(e)}")
            return False

    def retrieve_memory(self, memory_type: str, key: str = None, limit: int = 10):
        """Retrieve memories of a specific type"""
        from flask import current_app
        
        try:
            with current_app.app_context():
                query = Memory.query.filter_by(memory_type=memory_type)
                if key:
                    memory = query.filter_by(key=key).first()
                    if memory:
                        memory.last_accessed = datetime.utcnow()
                        db.session.commit()
                        return memory.value
                    return None
                
                memories = query.order_by(desc(Memory.confidence), desc(Memory.last_accessed)).limit(limit).all()
                return [{'key': m.key, 'value': m.value, 'confidence': m.confidence} for m in memories]
        except Exception as e:
            print(f"Error retrieving memory: {str(e)}")
            return None

    def update_pattern_confidence(self, memory_type: str, key: str, success: bool):
        """Update confidence of a pattern based on success/failure and historical performance"""
        from flask import current_app
        
        try:
            with current_app.app_context():
                memory = Memory.query.filter_by(memory_type=memory_type, key=key).first()
                if memory:
                    # Get current pattern statistics
                    pattern_stats = memory.value.get('stats', {
                        'total_attempts': 0,
                        'success_count': 0,
                        'failure_count': 0,
                        'consecutive_successes': 0,
                        'consecutive_failures': 0
                    })
                    
                    # Update statistics
                    pattern_stats['total_attempts'] += 1
                    if success:
                        pattern_stats['success_count'] += 1
                        pattern_stats['consecutive_successes'] += 1
                        pattern_stats['consecutive_failures'] = 0
                    else:
                        pattern_stats['failure_count'] += 1
                        pattern_stats['consecutive_failures'] += 1
                        pattern_stats['consecutive_successes'] = 0
                    
                    # Calculate new confidence based on success rate and consecutive outcomes
                    success_rate = pattern_stats['success_count'] / pattern_stats['total_attempts']
                    consecutive_bonus = min(0.1, 0.02 * pattern_stats['consecutive_successes'])
                    consecutive_penalty = min(0.2, 0.04 * pattern_stats['consecutive_failures'])
                    
                    # Adjust confidence
                    base_adjustment = 0.1 if success else -0.2
                    total_adjustment = base_adjustment + (consecutive_bonus if success else -consecutive_penalty)
                    
                    memory.confidence = max(0.1, min(1.0, success_rate + total_adjustment))
                    memory.value['stats'] = pattern_stats
                    memory.updated_at = datetime.utcnow()
                    
                    db.session.commit()
                    return True
                return False
        except Exception as e:
            if 'current_app' in locals():
                db.session.rollback()
            print(f"Error updating pattern confidence: {str(e)}")
            return False

    def store_transaction_pattern(self, pattern_key: str, pattern_data: dict):
        """Store a transaction pattern with metadata"""
        return self.store_memory(
            memory_type='transaction_pattern',
            key=pattern_key,
            value={
                'pattern': pattern_data,
                'success_count': 1,
                'last_success': datetime.utcnow().isoformat()
            }
        )

    def store_user_preference(self, preference_key: str, preference_value: dict):
        """Store user preferences"""
        return self.store_memory(
            memory_type='user_preference',
            key=preference_key,
            value=preference_value
        )

    def store_command_pattern(self, command_key: str, command_data: dict):
        """Store successful command patterns"""
        return self.store_memory(
            memory_type='command_pattern',
            key=command_key,
            value=command_data
        )

    def cleanup_old_memories(self, threshold_days: int = 30):
        """Clean up old memories with low confidence"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=threshold_days)
            Memory.query.filter(
                Memory.updated_at < cutoff_date,
                Memory.confidence < 0.3
            ).delete()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error cleaning up memories: {str(e)}")
            return False
